from django.test import Client, TestCase

from xorgauth.accounts.models import User, UserAlias


class AuthenticationTests(TestCase):
    def setUp(cls):
        cls.vaneau = User.objects.create_user(
            hrid='louis.vaneau.1829',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!'
        )
        UserAlias(user=cls.vaneau, email='vaneau@melix.net').save()

    def test_auth_hrid(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.1829'))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))

    def test_auth_hrid_badpass(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.1829'))
        c = Client()
        self.assertFalse(c.login(username='louis.vaneau.1829', password='Wrong password'))

    def test_auth_nonexisting_hrid(self):
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau.1830'))
        c = Client()
        self.assertFalse(c.login(username='louis.vaneau.1830', password='Depuis Vaneau!'))

    def test_auth_firstname_lastname(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau'))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau', password='Depuis Vaneau!'))

    def test_auth_homonym(self):
        c = Client()
        User.objects.create_user(
            hrid='louis.vaneau.m1829',
            main_email='louis.vaneau.d1829@doc.polytechnique.org',
            password='Depuis Vaneau!'
        )
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau'))
        self.assertFalse(c.login(username='louis.vaneau', password='Depuis Vaneau!'))

    def test_auth_main_email(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.1829@polytechnique.org'))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829@polytechnique.org', password='Depuis Vaneau!'))

    def test_auth_email_alias(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('vaneau@melix.net'))
        c = Client()
        self.assertTrue(c.login(username='vaneau@melix.net', password='Depuis Vaneau!'))

    def test_auth_nonexisting_email(self):
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau.1830@polytechnique.org'))
        c = Client()
        self.assertFalse(c.login(username='louis.vaneau.1830@polytechnique.org', password='Depuis Vaneau!'))
