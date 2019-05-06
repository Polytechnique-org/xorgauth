from django.test import Client, TestCase, override_settings
from django.urls import reverse

from xorgauth.accounts.models import User
from xorgauth.urls import urlpatterns as xorgauth_urlpatterns


class ViewTests(TestCase):
    # Views which are publicy accessible
    PUBLIC_VIEW_IDS = (
        'auth-groupex-login',
        'faq',
        'login',
        'logout',
        'test-relying-party',
        'password_reset',
        'password_reset_done',
        'password_reset_complete',
    )
    # Views which need an authenticated user
    LOGIN_REQUIRED_VIEW_IDS = (
        'auth-groupex',
        'index',
        'list_consents',
        'password_change',
        'password_change_done',
        'profile',
    )
    # Views which can not be tested because they need parameters
    PARAMETERIZED_VIEW_IDS = (
        'auth-groupex-logout',
        'password_reset_confirm',
        'sync-ax-data',
    )

    def test_know_all_views(self):
        """Check that every accessible view is either in PUBLIC_VIEW_IDS or in LOGIN_REQUIRED_VIEW_IDS"""
        known_views = set()
        known_views.update(self.PUBLIC_VIEW_IDS)
        known_views.update(self.LOGIN_REQUIRED_VIEW_IDS)
        known_views.update(self.PARAMETERIZED_VIEW_IDS)
        for urlpattern in xorgauth_urlpatterns:
            try:
                self.assertIn(urlpattern.name, known_views)
                known_views.remove(urlpattern.name)
            except AttributeError:
                pass
        # Ensure that every view in the local lists exist
        self.assertEqual(set(), known_views, "stray view IDs in tests")

    def test_public_views(self):
        """Test accessing publicy-accessible views"""
        for url_id in self.PUBLIC_VIEW_IDS:
            c = Client()
            resp = c.get(reverse(url_id))
            self.assertEqual(200, resp.status_code)

    def test_login_required_views_forbidden(self):
        """Test accessing login-required views without being logged in"""
        c = Client()
        for url_id in self.LOGIN_REQUIRED_VIEW_IDS:
            resp = c.get(reverse(url_id))
            self.assertEqual(302, resp.status_code,
                             "unexpected HTTP response code for URL %s" % url_id)
            if url_id == 'auth-groupex':
                self.assertTrue(resp['Location'].startswith('/auth-groupex-login?'),
                                "unexpected Location header: %r" % resp['Location'])
            else:
                self.assertTrue(resp['Location'].startswith('/accounts/login/?'),
                                "unexpected Location header: %r" % resp['Location'])

    def test_login_required_views_success(self):
        """Test accessing login-required views while being logged in"""
        # Create a dummy user
        User.objects.create_user(
            hrid='louis.vaneau.1829',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!',
        )
        for url_id in self.LOGIN_REQUIRED_VIEW_IDS:
            c = Client()
            self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
            resp = c.get(reverse(url_id))
            if resp.status_code == 302:
                self.assertFalse(resp['Location'].startswith(('/accounts/login/?', '/auth-groupex-login?')),
                                 "unexpected login-Location: %r" % resp['Location'])
            elif url_id == 'auth-groupex':
                self.assertEqual(400, resp.status_code,
                                 "unexpected HTTP response code for URL %s" % url_id)
            else:
                self.assertEqual(200, resp.status_code,
                                 "unexpected HTTP response code for URL %s" % url_id)

    @override_settings(MAINTENANCE=True)
    def test_public_views_maintenance(self):
        """Test accessing publicy-accessible views in maintenance mode"""
        self.test_public_views()

    @override_settings(MAINTENANCE=True)
    def test_login_required_views_forbidden_maintenance(self):
        """Test accessing login-required views without being logged in, in maintenance mode"""
        self.test_login_required_views_forbidden()

    @override_settings(MAINTENANCE=True)
    def test_login_required_views_success_maintenance(self):
        """Test accessing accessing login-required views while being logged in, in maintenance mode"""
        self.test_login_required_views_success()
