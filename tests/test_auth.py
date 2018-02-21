# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import crypt
import sys

from django.contrib import auth
from django.core import mail
from django.test import Client, TestCase
from django.utils import translation

from xorgauth.accounts.models import User, UserAlias
import xorgauth.forms


class AuthenticationTests(TestCase):
    def setUp(self):
        # Run tests in French in order to test translations
        translation.activate('fr')
        self.vaneau = User.objects.create_user(
            hrid='louis.vaneau.1829',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!'
        )
        UserAlias(user=self.vaneau, email='vaneau@melix.net').save()

    def test_auth_hrid(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.1829', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))

    def test_auth_hrid_badpass(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.1829', True))
        c = Client()
        self.assertFalse(c.login(username='louis.vaneau.1829', password='Wrong password'))

    def test_auth_hrid_disabled(self):
        self.vaneau.is_active = False
        self.vaneau.save()
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.1829', False))
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau.1829', True))
        c = Client()
        self.assertFalse(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))

    def test_auth_nonexisting_hrid(self):
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau.1830', True))
        c = Client()
        self.assertFalse(c.login(username='louis.vaneau.1830', password='Depuis Vaneau!'))

    def test_auth_firstname_lastname(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau', password='Depuis Vaneau!'))

    def test_auth_firstname_lastname_2_digits(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.29', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.29', password='Depuis Vaneau!'))

    def test_auth_homonym(self):
        c = Client()
        User.objects.create_user(
            hrid='louis.vaneau.d1829',
            main_email='louis.vaneau.d1829@doc.polytechnique.org',
            password='Depuis Vaneau!'
        )
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau', True))
        self.assertFalse(c.login(username='louis.vaneau', password='Depuis Vaneau!'))

    def test_auth_homonym_2_digits(self):
        c = Client()
        User.objects.create_user(
            hrid='louis.vaneau.1929',
            main_email='louis.vaneau.1929@polytechnique.org',
            password='Depuis Vaneau!'
        )
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau.29', True))
        self.assertFalse(c.login(username='louis.vaneau.29', password='Depuis Vaneau!'))

    def test_auth_main_email(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.1829@polytechnique.org', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829@polytechnique.org', password='Depuis Vaneau!'))

    def test_auth_email_alias(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('vaneau@melix.net', True))
        c = Client()
        self.assertTrue(c.login(username='vaneau@melix.net', password='Depuis Vaneau!'))

    def test_auth_nonexisting_email(self):
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau.1830@polytechnique.org', True))
        c = Client()
        self.assertFalse(c.login(username='louis.vaneau.1830@polytechnique.org', password='Depuis Vaneau!'))

    def test_googleapps_password(self):
        """Test setting the Google Apps password when setting the password"""
        self.vaneau.set_password('Depuis Vaneau!')
        self.vaneau.save()
        gapps_password = self.vaneau.gapps_password.password
        self.assertEqual(crypt.crypt('Depuis Vaneau!', gapps_password), gapps_password)

        password = 'Mot de passe différent?'
        self.vaneau.set_password(password)
        self.vaneau.save()
        self.vaneau = User.objects.get(hrid='louis.vaneau.1829')
        gapps_password = self.vaneau.gapps_password.password
        if sys.version_info < (3,):
            password = password.encode('utf-8')
        self.assertEqual(crypt.crypt(password, gapps_password), gapps_password)

    def test_password_reset_form(self):
        """Test using the password reset form"""
        form = xorgauth.forms.PasswordResetForm({
            'email': 'louis.vaneau.1829',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual('louis.vaneau.1829@polytechnique.org', form.cleaned_data['email'])
        form.save(domain_override='test.localhost')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual('Réinitialisation du mot de passe Polytechnique.org', mail.outbox[0].subject)
        self.assertEqual(['louis.vaneau.1829@polytechnique.org'], mail.outbox[0].to)

    def test_password_reset_form_unknown_user(self):
        """Test using the password reset form"""
        form = xorgauth.forms.PasswordResetForm({
            'email': 'louis.vaneau.1830',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual({
            'email': ['Compte utilisateur inconnu'],
        }, form.errors)
        self.assertEqual({}, form.cleaned_data)

    def test_password_reset_form_space(self):
        """Entering a space is invalid"""
        form = xorgauth.forms.PasswordResetForm({
            'email': ' ',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual({
            'email': ['Ce champ est obligatoire.'],
        }, form.errors)
        self.assertEqual({}, form.cleaned_data)

    def test_auth_session_expiry(self):
        c = Client()
        c.post('/accounts/login/', {'username': 'louis.vaneau.1829', 'password': 'Depuis Vaneau!', 'expiry': 'now'})
        self.assertTrue(auth.get_user(c).is_authenticated)
        self.assertTrue(c.session.get_expire_at_browser_close())
