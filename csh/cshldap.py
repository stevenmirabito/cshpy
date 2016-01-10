import ssl
import ldap3 as ldap
from csh.member import Member

USERS = 'ou=Users,dc=csh,dc=rit,dc=edu'
GROUPS = 'ou=Groups,dc=csh,dc=rit,dc=edu'
COMMITTEES = 'ou=Committees,dc=csh,dc=rit,dc=edu'
APPS = 'ou=Apps,dc=csh,dc=rit,dc=edu'


class LDAP:
    def __init__(self, user='', password='', host='ldap.csh.rit.edu', base=USERS, app=False, objects=False, debug=False):
        """
        Initializes object and binds to the specified LDAP server
        :param user: LDAP user to bind as
        :param password: Password for LDAP user
        :param host: LDAP server hostname
        :param base: Distinguished name base for user
        :param app: Connect as an app (boolean)
        :param objects: Convert results to csh.Member objects
        :param debug: Activate debug mode (boolean)
        :return: None
        """
        self.host = host
        self.base = base
        self.objects = objects
        self.debug = debug

        # Configure the LDAP server
        tls = ldap.Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1)
        self.ldap_server = ldap.Server(self.host, use_ssl=True, tls=tls)

        if user == '':
            # No user specified, use Kerberos via SASL/GSSAPI to bind
            self.ldap_conn = ldap.Connection(self.ldap_server, authentication=ldap.SASL, sasl_mechanism='GSSAPI')
        else:
            # Use simple authentication
            if app:
                # Use the APPS base rather than USERS or whatever was passed
                self.base = APPS

            # Construct user's distinguished name
            ldap_user_dn = 'uid={},{}'.format(user, self.base)

            # Set up the connection
            self.ldap_conn = ldap.Connection(self.ldap_server, user=ldap_user_dn, password=password)

        # Attempt to bind
        try:
            self.ldap_conn.bind()
        except ldap.LDAPException as e:
            print("Unable to bind to LDAP: " + str(e))
            if self.debug:
                print("[DEBUG] Connection details: " + str(self.ldap_conn))

    @staticmethod
    def _trim_result(result):
        return [x[1] for x in result]

    def eboard(self):
        """
        Returns a list of eboard members formatted as a search and inserts an extra ['committee'] attribute
        :return: List of csh.Member objects
        """
        # self.committee used as base because that's where eboard info is kept
        committees = self.search(base=COMMITTEES, cn='*')
        directors = []
        for committee in committees:
            for head in committee[1]['head']:
                director = self.search(dn=head)[0]
                director[1]['committee'] = committee[1]['cn'][0]
                directors.append(director)

        if self.objects:
            return self.member_objects(directors)

        return directors

    def group(self, group_cn):
        """
        Searches for and returns a list of all the members who belong to a certain group.
        :param group_cn: Group common name
        :return: List of csh.Member objects
        """
        group = self.search(base=GROUPS, cn=group_cn)

        if len(group) == 0:
            return []
        else:
            group_members = group[0]['attributes']['member']

        members = []
        for member in group_members:
            members.append(self.search(dn=member))

        if self.objects:
            return self.member_objects(members)

        return members

    def get_drink_admins(self):
        """
        Searches for all drink admins.
        :return: List of drink admin UIDs
        """
        admins = self.group('drink')
        return admins

    def get_groups(self, member_dn):
        """
        Returns a list of groups that a member belongs to.
        :param member_dn: Distinguished name of member
        :return: List of groups (as strings)
        """
        search_result = self.search(base=GROUPS, member=member_dn)

        if len(search_result) == 0:
            return []

        group_list = []
        for group in search_result:
            group_cn = group['attributes']['cn'][0]

            if self.debug:
                print("[DEBUG] User {} belongs to group: {}".format(member_dn, group_cn))

            group_list.append(group_cn)

        return group_list

    def get_rtps(self):
        """
        Searches for all RTPs
        :return: List of RTP UIDs
        """
        rtps = self.group('rtp')
        return rtps

    def member(self, uid):
        """
        Searches LDAP for a user
        :param uid: UID to search for
        :return: Dictionary of attributes
        """
        try:
            member = self.search(uid=uid)[0]
        except IndexError:
            return None

        if self.objects:
            return member

        return member[1]

    def members(self, uid='*'):
        """
        Issues an LDAP query for all users, and returns a dict for each matching entry.
        This can be quite slow, and takes roughly 3s to complete. You may optionally
        restrict the scope by specifying a uid, which is roughly equivalent to a search(uid='foo').
        :param uid: UID to search for (optional)
        :return: Dictionary of csh.Member objects
        """
        entries = self.search(uid)

        if self.objects:
            return self.member_objects(entries)

        result = []
        for entry in entries:
            result.append(entry[1])

        return result

    def member_objects(self, search_results):
        results = []

        for result in search_results:
            new_member = Member(result, ldap=self)
            results.append(new_member)

        return results

    def modify(self, uid, base=USERS, **kwargs):
        dn = 'uid={},{}'.format(uid, base)
        old_attrs = self.member(uid)
        mods_dict = {}

        for field, value in kwargs.items():
            if field in old_attrs:
                mods_dict[field] = [(ldap.MODIFY_REPLACE, [value])]

        self.ldap_conn.modify(dn, mods_dict)

    def search(self, base=USERS, trim=False, **kwargs):
        """
        Returns matching entries for search in ldap structured as [(dn, {attributes})]
        UNLESS searching by dn, in which case the first match is returned.
        :param base: Distinguished name base to use (optional, default is USERS)
        :param trim: Return a trimmed result (boolean)
        :return: Returns a list of LDAP search results
        """
        search_filter = ''
        for key, value in kwargs.items():
            if isinstance(value, list):
                search_filter += '(|'
                for term in value:
                    term = term.replace('(', '\\(')
                    term = term.replace(')', '\\)')
                    search_filter += '({0}={1})'.format(key, term)
                search_filter += ')'
            else:
                value = value.replace('(', '\\(')
                value = value.replace(')', '\\)')
                search_filter += '({0}={1})'.format(key, value)

            if key == 'dn':
                search_filter = '(objectClass=*)'
                base = value
                break

        if len(kwargs) > 1:
            search_filter = '(&' + search_filter + ')'

        result = self.ldap_conn.search(search_base=base, search_filter=search_filter, attributes=['*', '+'])
        if result:
            if base == USERS:
                for member in self.ldap_conn.response:
                    if self.debug:
                        print("[DEBUG] Entry: " + str(member))

                    groups = self.get_groups(member['dn'])
                    member['attributes']['groups'] = groups

                    if 'eboard' in member['attributes']['groups']:
                        eboard_search = self.search(base=COMMITTEES, head=member['dn'])

                        if eboard_search:
                            member.committee = self.ldap_conn.reponse[0]['attributes']['cn']

            if self.objects:
                return self.member_objects(self.ldap_conn.response)

            final_result = self._trim_result(self.ldap_conn.response) if trim else self.ldap_conn.response
        else:
            final_result = []

        return final_result
