import requests
import json


class Webnews:
    def __init__(self, api_key, api_agent='A script using webnews.py'):
        self.payload = {'api_key': api_key, 'api_agent': api_agent}
        self.headers = {'Accept': 'application/json'}
        self.prefix = 'https://webnews.csh.rit.edu/'

    def _get(self, target, params=None):
        if not params:
            params = {}

        url = self.prefix + target
        payload = dict(self.payload, **params)

        return requests.get(url, params=payload, headers=self.headers, verify=False)

    def _post(self, target, params=None):
        if not params:
            params = {}

        url = self.prefix + target
        payload = dict(self.payload, **params)

        return requests.post(url, params=payload, headers=self.headers, verify=False)

    def _put(self, target, params=None):
        if not params:
            params = {}

        url = self.prefix + target
        payload = dict(self.payload, **params)

        return requests.put(url, params=payload, headers=self.headers, verify=False)

    def _delete(self, target, params=None):
        if not params:
            params = {}

        url = self.prefix + target
        payload = dict(self.payload, **params)

        return requests.delete(url, params=payload, headers=self.headers, verify=False)

    def newsgroups(self):
        return self._get('newsgroups')

    def newsgroup_names(self):
        names = []
        group_dicts = json.loads(self.newsgroups().content)['newsgroups']

        for group_dict in group_dicts:
            name = group_dict[u'name']
            names.append(name)

        return names

    def search(self, more=True, **kwargs):
        while more:
            r = json.loads(self._get('search', params=kwargs).content)
            posts = r['posts_older']
            more = r['more_older']
            if more:
                kwargs['from_older'] = posts[-1]['post']['date']
            yield posts

    def user(self):
        return json.loads(self._get('user').content)['user']

    def news_post(self, newsgroup, num):
        r = self._get(newsgroup + '/' + str(num), {'html_body': True})
        return json.loads(r.content)['post']

    def get_unread_counts(self):
        return json.loads(self._get('unread_counts').content)['unread_counts']

    def get_newsgroup_index(self, newsgroup):
        return json.loads(self._get(newsgroup + '/index', {'newsgroup': newsgroup}).content)

    @staticmethod
    def get_last_date(posts):
        return posts[-1][u'post'][u'date']

    def compose(self, newsgroup, subject, **kwargs):
        kwargs['newsgroup'] = newsgroup
        kwargs['subject'] = subject
        self._post('compose', params=kwargs)

    def mark_read(self, **kwargs):
        self._put('mark_read', kwargs)

    def stick(self, newsgroup, number, time):
        self._put(newsgroup + '/' + number + '/sticky', {'sticky_until': time})

    def unstick(self, newsgroup, number):
        self._put(newsgroup + '/' + number + '/sticky', {'unstick': True})

    def star(self, newsgroup, number):
        self._put(newsgroup + '/' + number + '/star')

    def delete_post(self, newsgroup, number, reason='I do what I want'):
        params = {'reason': reason, 'confirm_cancel': True, 'posting_host': 'wannamaker'}
        self._delete(newsgroup + '/' + str(number), params)

    def activity(self):
        a = self._get('activity')
        return json.loads(a.content)['activity']
