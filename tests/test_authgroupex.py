# -*- coding: utf-8 -*-
import hashlib
import random
import struct

import django
from django import http
import django.contrib.auth
from django.test import Client, TestCase
from django.urls import reverse

from xorgauth.accounts.models import User, UserAlias, Role, Group, GroupMembership
from xorgauth.authgroupex.models import AuthGroupeXClient
import xorgauth.authgroupex.views as authgroupex_views


class AuthGroupeXTests(TestCase):

    def setUp(cls):
        cls.client_simple = AuthGroupeXClient.objects.create(
            privkey='356a192b7913b04c54574d18c28d46e6395428ab',  # SHA1("1")
            name='Test AuthGroupeX Client',
            data_fields='matricule_ax,nom,prenom,full_promo,forlife,sex',
            return_urls=r'#https://example\.com/#',
            allow_xnet=False,
        )

        vaneau = User.objects.create_user(
            hrid='louis.vaneau.1829',
            fullname='Louis Vaneau',
            firstname='Louis',
            lastname='Vaneau',
            sex='male',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!',
            axid='18290001',
            schoolid='18290042',
            xorgdb_uid=1,
            study_year='X1829',
            grad_year=1832,
        )
        cls.role_x = Role.objects.create(hrid='x', display='X')
        cls.role_xnet = Role.objects.create(hrid='xnet', display='External')
        vaneau.roles.add(cls.role_x)
        vaneau.save()
        UserAlias(user=vaneau, email='vaneau@melix.net').save()

    @staticmethod
    def _get_logout_req_url(privkey, return_url, session=None):
        """Generate a request challenge for logout and compute its signature"""
        challenge = hashlib.sha1(
            b''.join(struct.pack(b'B', random.randrange(0, 256)) for i in range(64)))
        challenge = challenge.hexdigest()
        sig = hashlib.md5((challenge + privkey).encode('ascii')).hexdigest()
        query = http.QueryDict('', mutable=True)
        query['challenge'] = challenge
        query['pass'] = sig
        query['url'] = return_url
        if session:
            query['session'] = session
        requrl = reverse('auth-groupex-logout') + '?' + query.urlencode()
        return requrl, challenge

    @staticmethod
    def _get_req_url(privkey, return_url, group=None):
        """Generate a request challenge and compute its signature"""
        challenge = hashlib.sha1(
            b''.join(struct.pack(b'B', random.randrange(0, 256)) for i in range(64)))
        challenge = challenge.hexdigest()
        sig = hashlib.md5((challenge + privkey).encode('ascii')).hexdigest()
        query = http.QueryDict('', mutable=True)
        query['challenge'] = challenge
        query['pass'] = sig
        query['url'] = return_url
        if group:
            query['group'] = group
        requrl = reverse('auth-groupex') + '?' + query.urlencode()
        return requrl, challenge

    def _check_resp_auth(self, privkey, return_url, challenge, location, additional_fields=None):
        """Check that the response has the right authorization result"""
        self.assertTrue(location.startswith(return_url + '?'),
                        "unexpected Location header: %r" % location)
        query_params = http.QueryDict(location[len(return_url) + 1:])

        # Compute expected auth
        check_str = '1%s%s' % (challenge, privkey)
        known_resp_fields = set(('auth', ))
        if additional_fields:
            known_resp_fields.update(additional_fields)
        for field in self.client_simple.data_fields.split(','):
            self.assertTrue(field in query_params, "missing field %r in response" % field)
            check_str += query_params[field]
            known_resp_fields.add(field)
        check_str += '1'
        expected_auth = hashlib.md5(check_str.encode('utf-8')).hexdigest()
        self.assertEqual(known_resp_fields, set(query_params.keys()),
                         "unexpected fields in response")
        return query_params, expected_auth

    @staticmethod
    def _is_user_authenticated(client):
        """Is the user of the given client object authenticated?"""
        user = django.contrib.auth.get_user(client)
        return user.is_authenticated if django.VERSION >= (1, 10) else user.is_authenticated()

    def test_unlogged_request(self):
        requrl, challenge = self._get_req_url(self.client_simple.privkey, 'https://example.com/')

        c = Client()
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        login_url = reverse('auth-groupex-login')
        self.assertTrue(resp['Location'].startswith(login_url + '?'),
                        "unexpected Location header: %r" % resp['Location'])
        query_params = http.QueryDict(resp['Location'][len(login_url) + 1:])
        self.assertEqual(['next'], list(query_params.keys()))
        self.assertEqual(requrl, query_params['next'])

    def test_logged_request(self):
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey, 'https://example.com/')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        query_params, expected_auth = self._check_resp_auth(
            self.client_simple.privkey, 'https://example.com/', challenge, resp['Location'])
        self.assertEqual(query_params.dict(), {
            'auth': expected_auth,
            'forlife': 'louis.vaneau.1829',
            'full_promo': 'X1829',
            'matricule_ax': '18290001',
            'nom': 'Vaneau',
            'prenom': 'Louis',
            'sex': 'male',
        })

    def test_logged_request_2(self):
        self.client_simple.data_fields = 'matricule,uid,username,firstname,lastname,forlife,entry_year,grad_year,perms'
        self.client_simple.save()

        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey, 'https://example.com/')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        query_params, expected_auth = self._check_resp_auth(
            self.client_simple.privkey, 'https://example.com/', challenge, resp['Location'])
        self.assertEqual(query_params.dict(), {
            'auth': expected_auth,
            'uid': '1',
            'username': 'louis.vaneau.1829@polytechnique.org',
            'firstname': 'Louis',
            'lastname': 'Vaneau',
            'matricule': '18290042',
            'forlife': 'louis.vaneau.1829',
            'entry_year': '1829',
            'grad_year': '1832',
            'perms': 'user',
        })

    def test_unicode_return_url(self):
        """Test returning from the authentication with an Unicode URL"""
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey, 'https://example.com/→«àéîöùÿ»‽?!=😇&☀=★')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        query_params, expected_auth = self._check_resp_auth(
            self.client_simple.privkey,
            'https://example.com/%E2%86%92%C2%AB%C3%A0%C3%A9%C3%AE%C3%B6%C3%B9%C3%BF%C2%BB%E2%80%BD',
            challenge,
            resp['Location'],
            additional_fields=('!', '☀'))
        self.assertEqual(query_params.dict(), {
            'auth': expected_auth,
            'forlife': 'louis.vaneau.1829',
            'full_promo': 'X1829',
            'matricule_ax': '18290001',
            'nom': 'Vaneau',
            'prenom': 'Louis',
            'sex': 'male',
            '!': '😇',
            '☀': '★',
        })

    def test_logged_request__groupadm(self):
        grp = Group.objects.create(shortname='X1829')
        grp.save()
        user = User.objects.get(hrid='louis.vaneau.1829')
        gmem = GroupMembership.objects.create(group=grp, user=user, perms='admin')
        gmem.save()
        self.client_simple.data_fields = 'forlife,perms,grpauth'
        self.client_simple.save()

        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey,
                                              'https://example.com/',
                                              group='X1829')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        query_params, expected_auth = self._check_resp_auth(
            self.client_simple.privkey, 'https://example.com/', challenge, resp['Location'])
        self.assertEqual(query_params.dict(), {
            'auth': expected_auth,
            'forlife': 'louis.vaneau.1829',
            'perms': 'user',
            'grpauth': 'admin',
        })

    def test_logged_request_group_member(self):
        grp = Group.objects.create(shortname='X1829')
        grp.save()
        user = User.objects.get(hrid='louis.vaneau.1829')
        gmem = GroupMembership.objects.create(group=grp, user=user, perms='member')
        gmem.save()
        self.client_simple.data_fields = 'forlife,perms,grpauth'
        self.client_simple.save()

        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey,
                                              'https://example.com/',
                                              group='X1829')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        query_params, expected_auth = self._check_resp_auth(
            self.client_simple.privkey, 'https://example.com/', challenge, resp['Location'])
        self.assertEqual(query_params.dict(), {
            'auth': expected_auth,
            'forlife': 'louis.vaneau.1829',
            'perms': 'user',
            'grpauth': 'membre',
        })

    def test_logged_request_no_group_member(self):
        self.client_simple.data_fields = 'forlife,perms,grpauth'
        self.client_simple.save()

        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey,
                                              'https://example.com/',
                                              group='X1829')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        query_params, expected_auth = self._check_resp_auth(
            self.client_simple.privkey, 'https://example.com/', challenge, resp['Location'])
        self.assertEqual(query_params.dict(), {
            'auth': expected_auth,
            'forlife': 'louis.vaneau.1829',
            'perms': 'user',
            'grpauth': '',
        })

    def test_unknown_site(self):
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey, 'https://unknown.example.com/')
        resp = c.get(requrl)
        self.assertEqual(400, resp.status_code)

    def test_xnet_on_non_xnet_site(self):
        user = User.objects.get(hrid='louis.vaneau.1829')
        user.roles.clear()
        user.roles.add(self.role_xnet)
        user.save()
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey, 'https://example.com/')
        resp = c.get(requrl)
        self.assertEqual(403, resp.status_code)

    def test_xnet_on_xnet_site(self):
        user = User.objects.get(hrid='louis.vaneau.1829')
        user.roles.clear()
        user.roles.add(self.role_xnet)
        user.save()
        self.client_simple.allow_xnet = True
        self.client_simple.save()

        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        requrl, challenge = self._get_req_url(self.client_simple.privkey, 'https://example.com/')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        query_params, expected_auth = self._check_resp_auth(
            self.client_simple.privkey, 'https://example.com/', challenge, resp['Location'])
        self.assertEqual(query_params.dict(), {
            'auth': expected_auth,
            'forlife': 'louis.vaneau.1829',
            'full_promo': 'X1829',
            'matricule_ax': '18290001',
            'nom': 'Vaneau',
            'prenom': 'Louis',
            'sex': 'male',
        })

    def test_regexp_site(self):
        self.client_simple.return_urls = r'#^https?://(dev|preprod|www)\.example\.(net|org)/#'
        self.client_simple.save()

        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))

        for url in ('http://dev.example.net/', 'https://www.example.org/', 'https://preprod.example.org/'):
            requrl, challenge = self._get_req_url(self.client_simple.privkey, url)
            resp = c.get(requrl)
            self.assertEqual(302, resp.status_code, "error for URL %r" % url)
            query_params, expected_auth = self._check_resp_auth(
                self.client_simple.privkey, url, challenge, resp['Location'])
            self.assertEqual(query_params.dict(), {
                'auth': expected_auth,
                'forlife': 'louis.vaneau.1829',
                'full_promo': 'X1829',
                'matricule_ax': '18290001',
                'nom': 'Vaneau',
                'prenom': 'Louis',
                'sex': 'male',
            })

    def test_logout_request(self):
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        self.assertTrue(self._is_user_authenticated(c))

        # Test the logout endpoint
        requrl, _ = self._get_logout_req_url(self.client_simple.privkey, 'https://example.com/logout')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        self.assertEqual('https://example.com/logout', resp['Location'])

        # Ensure that the user is disconnected
        self.assertFalse(self._is_user_authenticated(c))

    def test_logout_phpsession_request(self):
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        self.assertTrue(self._is_user_authenticated(c))

        requrl, _ = self._get_logout_req_url(
            self.client_simple.privkey,
            'https://example.com/logout',
            session='0123456789')
        resp = c.get(requrl)
        self.assertEqual(302, resp.status_code)
        self.assertEqual('https://example.com/logout?PHPSESSID=0123456789', resp['Location'])
        self.assertFalse(self._is_user_authenticated(c))

    def test_logout_unknown_url(self):
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        self.assertTrue(self._is_user_authenticated(c))

        # Test the logout endpoint
        requrl, _ = self._get_logout_req_url(self.client_simple.privkey, 'https://unknown.example.com/logout')
        resp = c.get(requrl)
        self.assertEqual(400, resp.status_code)
        self.assertNotIn('Location', resp)
        self.assertTrue(self._is_user_authenticated(c))

    def test_logout_incorrect_secret(self):
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        self.assertTrue(self._is_user_authenticated(c))

        # Test the logout endpoint
        requrl, _ = self._get_logout_req_url(self.client_simple.privkey + '!', 'https://example.com/logout')
        resp = c.get(requrl)
        self.assertEqual(400, resp.status_code)
        self.assertNotIn('Location', resp)
        self.assertTrue(self._is_user_authenticated(c))

    def test_displayed_url(self):
        """Test the URL displayed in the login page"""
        # Wikix through old Polytechnique.org
        next_value = '/auth-groupex?session=0123456789'
        next_value += '&challenge=0123456789abcdef0123456789abcdef01234567'
        next_value += '&pass=0123456789abcdef0123456789abcdef01234567'
        next_value += '&url=https%3A%2F%2Fwww.polytechnique.org%2Fauth-groupex'
        next_value += '%3Fchallenge%3Dfedcba9876543210%26pass%3Dfedcba9876543210'
        next_value += '%26url%3Dhttps%3A%2F%2Fwikix.polytechnique.org%2FSpecial%3AUserlogin'
        next_value += '%3Freturnto%3DAccueil'
        self.assertEqual(
            'https://www.polytechnique.org/auth-groupex?challenge=fedcba9876543210&pass=fedcb...',
            authgroupex_views.extract_url_from_next_param(next_value, cut_length=80))

        # forum.polytechnique.org
        next_value = '/auth-groupex?session=0123456789'
        next_value += '&challenge=0123456789abcdef0123456789abcdef01234567'
        next_value += '&pass=0123456789abcdef0123456789abcdef01234567'
        next_value += '&url=https%3A%2F%2Fwww.polytechnique.org%2Fauth-discourse%2Fforum.polytechnique.org'
        next_value += '%3Fsso%3Dbase64blabla%253D%250A%26sig%3Dxyz'
        self.assertEqual(
            'https://www.polytechnique.org/auth-discourse/forum.polytechnique.org?sso=base64blabla%3D%0A&sig=xyz',
            authgroupex_views.extract_url_from_next_param(next_value))

        # x-suisse.polytechnique.org, with Unicode issues
        next_value = '/auth-groupex?session=0123456789'
        next_value += '&challenge=0123456789abcdef0123456789abcdef01234567'
        next_value += '&pass=0123456789abcdef0123456789abcdef01234567'
        next_value += '&group=x-suisse'
        next_value += '&url=https%3A%2F%2Fx-suisse.polytechnique.org%2Fauth%2FXorgReturn'
        next_value += '%3Fpath%3D%2Ffeed%2Fcategory%2FG%C3%A9n%C3%A9ral%2Fatom'
        self.assertEqual(
            'https://x-suisse.polytechnique.org/auth/XorgReturn?path=/feed/category/Général/atom',
            authgroupex_views.extract_url_from_next_param(next_value))
