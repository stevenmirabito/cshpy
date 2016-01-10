cshpy
=====

A collection of Python 3 utilities and wrappers for services run by [Computer Science House](http://csh.rit.edu/) at RIT.

## Installation

    $ pip install cshpy3

(or just download the source)

## Basic Usage
```python
#!/usr/bin/python
from csh.cshldap import LDAP

# Creates a connection to CSH's LDAP server as an object with some helper functions
# You can also omit the username and password to bind with a Kerberos ticket
ldap = LDAP('<user>','<password>')

# Returns a list of results, in this case of users whose uid starts with 'duck'.
# All CSH LDAP fields are included in a similar way.
ldap.search(uid='duck*')

# This will return users whose common names (cn) start with 'Chris'
ldap.search(cn='Chris')

# This will return users whose uid starts with 'user', and cn starts with 'Name'
ldap.search(uid='user*', cn='Name*')

# Returns a dict of a user's attributes. Performs a search, and then grabs the first result.
# Are you feelin' lucky?
ldap.member('uidValue')

# Equivalent to search(uid='*')
ldap.members()

# You may optionally include a search string.
# Equivalent to search(uid='username')
ldap.members('test')
```

## Functions

### search()

Search returns a list of tuples containing a string and a dictionary.
The first element of each tuple is the Distinguished Name (dn) of the entry.
This is the path to the entry in ldap. The second element of each tuple is a
dictionary of attributes as keys.

Specific tweaks for CSH include the insertion of two fields, `groups` and `committee`.
If a member is on eboard, `committee` will have the name of their committee. Otherwise,
this field will not be present.
`groups` will contain a list of all the groups a member belongs to.

So to be clear the return looks like this: `[('dn',{attributes})]`

You may optionally specify a different base than the default. `search(base=...)`

####Word of caution: Not all results are guaranteed to have the same attribute fields
in their dictionary. Do not depend on all users having a `twitterName` for example.

### modify(uid, attr1=val1, attr2=val2)

Given a uid, and attribute values, modifies those values in ldap.
You may optionally specify a base other than Users.

### member(uid)

Returns a dict of attributes for the user. Equivalent to `search(uid=uid)[0][1]`.

### members()

Returns a list of users. Shorthand for `search(uid='*')`, or some variant *

### group(cn)
Searches groups by common name, returns a list of users in that group.

### getGroups(dn)
Returns a list of cns for groups the given member is a part of.

### rtps()

Returns a list of rtps. Shorthand for `group('rtp')`

### drinkAdmins()

Returns a list of drink admins. Shorthand for `group('drink')`

### eboard()

Returns a list of eboard members. Shorthand for `group('eboard')`