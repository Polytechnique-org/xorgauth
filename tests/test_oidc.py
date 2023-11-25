import json
import sys
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

import oidc_provider.models

from xorgauth.accounts.models import User, UserAlias

if sys.version_info >= (3,):
    import urllib.parse
else:
    import urlparse

    class urllib(object):
        parse = urlparse


class AuthenticationTests(TestCase):
    def setUp(self):
        call_command('creatersakey')

        client_public_noconsent = oidc_provider.models.Client(
            name='Test Client',
            client_id='123456789',
            client_type='public',
            client_secret='',
            redirect_uris=['http://example.com/'],
            require_consent=False)
        client_public_noconsent.save()

        response_type = oidc_provider.models.ResponseType.objects.get(value='id_token token')
        client_public_noconsent.response_types.add(response_type)

        self.vaneau = User.objects.create_user(
            hrid='louis.vaneau.1829',
            fullname='Louis Vaneau',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!',
            axid='18290001',
            study_year='X1829',
            grad_year=1829,
        )
        UserAlias(user=self.vaneau, email='vaneau@melix.net').save()

    def _request_access_token(self, client, scopes):
        self.assertTrue(client.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        response = client.get(reverse('oidc_provider:authorize'), {
            'client_id': '123456789',
            'redirect_uri': 'http://example.com/',
            'response_type': 'id_token token',
            'scope': scopes,
            'nonce': 'abcdef',
        })
        self.assertEqual(302, response.status_code)
        loc = response['location']
        self.assertEqual('http://example.com/', loc.split('#')[0],
                         "invalid Location header: %r" % loc)
        query_values = urllib.parse.parse_qs(loc.split('#', 1)[1])
        self.assertIn('access_token', query_values.keys())
        return query_values['access_token'][0]

    def test_userinfo(self):
        """Test requesting OIDC user info"""
        c = Client()
        access_token = self._request_access_token(c, 'openid profile email')

        response = c.get(reverse('oidc_provider:userinfo'), {
            'access_token': access_token,
        })
        self.assertEqual(200, response.status_code)
        userinfo = json.loads(response.content.decode('utf-8'))
        self.assertEqual({
            'sub': 'louis.vaneau.1829',
            'name': 'Louis Vaneau',
            'email': 'louis.vaneau.1829@polytechnique.org',
        }, userinfo)

    def test_axid(self):
        """Test acquiring AX ID through OIDC"""
        c = Client()
        access_token = self._request_access_token(c, 'openid profile email xorg_axid')

        response = c.get(reverse('oidc_provider:userinfo'), {
            'access_token': access_token,
        })
        self.assertEqual(200, response.status_code)
        userinfo = json.loads(response.content.decode('utf-8'))
        self.assertEqual({
            'sub': 'louis.vaneau.1829',
            'name': 'Louis Vaneau',
            'email': 'louis.vaneau.1829@polytechnique.org',
            'axid': '18290001',
        }, userinfo)

    def test_axid_mangled_query(self):
        client = Client()
        self.assertTrue(client.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        response = client.get(reverse('oidc_provider:authorize'), {
            'amp;client_id': '123456789',
            'amp;redirect_uri': 'http://example.com/',
            'amp;response_type': 'id_token token',
            'amp;scope': 'openid profile email xorg_axid',
            'amp;nonce': 'abcdef',
        })
        self.assertEqual(302, response.status_code)
        loc = response['location']
        self.assertEqual('http://example.com/', loc.split('#')[0],
                         "invalid Location header: %r" % loc)
        query_values = urllib.parse.parse_qs(loc.split('#', 1)[1])
        self.assertIn('access_token', query_values.keys())
        access_token = query_values['access_token'][0]

        response = client.get(reverse('oidc_provider:userinfo'), {
            'access_token': access_token,
        })
        self.assertEqual(200, response.status_code)
        userinfo = json.loads(response.content.decode('utf-8'))
        self.assertEqual({
            'sub': 'louis.vaneau.1829',
            'name': 'Louis Vaneau',
            'email': 'louis.vaneau.1829@polytechnique.org',
            'axid': '18290001',
        }, userinfo)

    def test_study_years(self):
        """Test acquiring study years through OIDC"""
        c = Client()
        access_token = self._request_access_token(c, 'openid profile email xorg_study_years')

        response = c.get(reverse('oidc_provider:userinfo'), {
            'access_token': access_token,
        })
        self.assertEqual(200, response.status_code)
        userinfo = json.loads(response.content.decode('utf-8'))
        self.assertEqual({
            'sub': 'louis.vaneau.1829',
            'name': 'Louis Vaneau',
            'email': 'louis.vaneau.1829@polytechnique.org',
            'study_years': ['X1829'],
        }, userinfo)

    def test_axinfo(self):
        """Test acquiring AX information through OIDC"""
        c = Client()
        access_token = self._request_access_token(c, 'openid profile email xorg_axinfo')
        response = c.get(reverse('oidc_provider:userinfo'), {
            'access_token': access_token,
        })
        self.assertEqual(200, response.status_code)
        userinfo = json.loads(response.content.decode('utf-8'))
        # At first, there is no information => no new information
        self.assertEqual({
            'sub': 'louis.vaneau.1829',
            'name': 'Louis Vaneau',
            'email': 'louis.vaneau.1829@polytechnique.org',
        }, userinfo)

        # Then, fill some information
        self.vaneau.ax_contributor = True
        self.vaneau.axjr_subscriber = True
        self.vaneau.save()
        access_token = self._request_access_token(c, 'openid profile email xorg_axinfo')
        response = c.get(reverse('oidc_provider:userinfo'), {
            'access_token': access_token,
        })
        self.assertEqual(200, response.status_code)
        userinfo = json.loads(response.content.decode('utf-8'))
        self.assertEqual({
            'sub': 'louis.vaneau.1829',
            'name': 'Louis Vaneau',
            'email': 'louis.vaneau.1829@polytechnique.org',
            'ax_contributor': True,
            'axjr_subscriber': True,
        }, userinfo)
