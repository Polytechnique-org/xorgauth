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
        # Add classic aliases
        UserAlias(user=self.vaneau, email='louis.vaneau@polytechnique.org').save()
        UserAlias(user=self.vaneau, email='louis.vaneau.29@polytechnique.org').save()
        UserAlias(user=self.vaneau, email='louis.vaneau@m4x.org').save()
        UserAlias(user=self.vaneau, email='louis.vaneau.29@m4x.org').save()
        UserAlias(user=self.vaneau, email='louis.vaneau.1829@m4x.org').save()

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

    def test_auth_non_lowercase_hrid(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('lOuIs.vANeaU.1829', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))

    def test_auth_nonexisting_hrid(self):
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau.1830', True))
        c = Client()
        self.assertFalse(c.login(username='louis.vaneau.1830', password='Depuis Vaneau!'))

    def test_auth_firstname_lastname(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau', password='Depuis Vaneau!'))

    def test_auth_firstname_lastname_non_lowercase(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('loUIs.vANEau', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau', password='Depuis Vaneau!'))

    def test_auth_main_email(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.1829@polytechnique.org', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829@polytechnique.org', password='Depuis Vaneau!'))

    def test_auth_main_email_non_lowercase(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louiS.VaneaU.1829@pOLYTechnIQUE.org', True))
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

    def test_auth_firstname_lastname_2_digits(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('louis.vaneau.29', True))
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.29', password='Depuis Vaneau!'))

    def test_auth_firstname_lastname_2_digits_non_lowercase(self):
        self.assertEqual(self.vaneau, User.objects.get_for_login('lOUIs.vANEau.29', True))
        c = Client()

        self.assertTrue(c.login(username='louis.vaneau.29', password='Depuis Vaneau!'))

    def test_auth_homonym_same_curriculum(self):
        c = Client()
        homonym = User.objects.create_user(
            hrid="louis.vaneau.1830",  # same name, same curriculum, different year
            main_email="louis.vaneau.1830@polytechnique.org",
            password="Depuis Vaneau again!"
        )
        UserAlias(user=homonym, email="louis.vaneau.30@polytechnique.org").save()
        UserAlias(user=homonym, email="louis.vaneau.30@m4x.org").save()
        UserAlias(user=homonym, email="louis.vaneau.1830@m4x.org").save()
        UserAlias.objects.filter(user=self.vaneau, email__startswith="louis.vaneau@").delete()
        self.assertEqual(None, User.objects.get_for_login("louis.vaneau", True))
        self.assertFalse(c.login(username='louis.vaneau', password='Depuis Vaneau!'))
        self.assertTrue(c.login(username='louis.vaneau.29', password='Depuis Vaneau!'))
        self.assertTrue(c.login(username='louis.vaneau.30', password='Depuis Vaneau again!'))

    def test_auth_homonym_different_curriculum(self):
        c = Client()
        homonym = User.objects.create_user(
            hrid='louis.vaneau.d1829',  # same name, same year, different curriculum
            main_email='louis.vaneau.d1829@doc.polytechnique.org',
            password='Depuis Dr. Vaneau!'
        )
        UserAlias(user=homonym, email="louis.vaneau@doc.polytechnique.org").save()
        UserAlias(user=homonym, email="louis.vaneau.d29@doc.polytechnique.org").save()
        UserAlias(user=homonym, email="louis.vaneau@doc.m4x.org").save()
        UserAlias(user=homonym, email="louis.vaneau.d29@doc.m4x.org").save()
        UserAlias(user=homonym, email="louis.vaneau.d1929@doc.m4x.org").save()
        self.assertIsNone(User.objects.get_for_login('louis.vaneau', True))
        self.assertFalse(c.login(username='louis.vaneau', password='Depuis Vaneau!'))
        self.assertTrue(c.login(username='louis.vaneau.29', password='Depuis Vaneau!'))
        self.assertTrue(c.login(username='louis.vaneau.d29', password='Depuis Dr. Vaneau!'))

    def test_auth_homonym_2_digits(self):
        c = Client()
        homonym = User.objects.create_user(
            hrid='louis.vaneau.1929',  # same name, same curriculum, different year but same "2 digits"
            main_email='louis.vaneau.1929@polytechnique.org',
            password='Depuis Vaneau!'
        )
        UserAlias(user=homonym, email="louis.vaneau.1929@m4x.org").save()
        UserAlias.objects.filter(user=self.vaneau, email__startswith="louis.vaneau@").delete()
        UserAlias.objects.filter(user=self.vaneau, email__startswith="louis.vaneau.29@").delete()
        self.assertEqual(None, User.objects.get_for_login('louis.vaneau.29', True))
        self.assertFalse(c.login(username='louis.vaneau.29', password='Depuis Vaneau!'))

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

    def test_password_set_form(self):
        """Test using the password set form"""
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        form = xorgauth.forms.SetPasswordForm(user=self.vaneau, data={
            'new_password1': 'Mot de passe différent?',
            'new_password2': 'Mot de passe différent?',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual('Mot de passe différent?', form.cleaned_data['new_password1'])
        form.save()
        # Athentication with the previous password fails and it works with the new password
        self.assertFalse(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Mot de passe différent?'))

    def test_password_change_form(self):
        """Test using the password change form"""
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        form = xorgauth.forms.PasswordChangeForm(user=self.vaneau, data={
            'old_password': 'Depuis Vaneau!',
            'new_password1': 'Mot de passe différent?',
            'new_password2': 'Mot de passe différent?',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual('Mot de passe différent?', form.cleaned_data['new_password1'])
        form.save()
        # Athentication with the previous password fails and it works with the new password
        self.assertFalse(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Mot de passe différent?'))

    def test_password_change_form_incorrect_oldpass(self):
        """Test using the password change form with an incorrect old password"""
        c = Client()
        self.assertTrue(c.login(username='louis.vaneau.1829', password='Depuis Vaneau!'))
        form = xorgauth.forms.PasswordChangeForm(user=self.vaneau, data={
            'old_password': 'Depuis Vaneau?',
            'new_password1': 'Mot de passe différent?',
            'new_password2': 'Mot de passe différent?',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual({
            'old_password': ['Votre ancien mot de passe est incorrect. Veuillez le rectifier.'],
        }, form.errors)
        self.assertEqual({
            'new_password1': 'Mot de passe différent?',
            'new_password2': 'Mot de passe différent?',
        }, form.cleaned_data)

    def test_auth_session_expiry(self):
        c = Client()
        c.post('/accounts/login/', {'username': 'louis.vaneau.1829', 'password': 'Depuis Vaneau!', 'expiry': 'now'})
        self.assertTrue(auth.get_user(c).is_authenticated)
        self.assertTrue(c.session.get_expire_at_browser_close())
