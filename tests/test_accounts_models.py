from django.core.exceptions import ValidationError
from django.test import TestCase

from xorgauth.accounts.models import User, UserAlias


class AccountsModelTests(TestCase):
    """Test accounts models consistency"""

    def test_dead_user(self):
        """Test modifying the death date"""
        user = User.objects.create_user(
            hrid='louis.vaneau.1829',
            fullname='Louis Vaneau',
            preferred_name='Louis Vaneau',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!'
        )
        user.full_clean()

        # Defining the death date makes the user dead
        self.assertFalse(user.is_dead)
        user.death_date = '1830-07-29'
        user.full_clean()
        self.assertTrue(user.is_dead)

    def test_non_lowercase_hruid(self):
        """Test using non-lowercase human-readable IDss"""
        user = User(
            hrid='louis.vaneau.1829',
            fullname='Louis Vaneau',
            preferred_name='Louis Vaneau',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!'
        )
        user.full_clean()
        user.hrid = 'Louis.Vaneau.1829'
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_non_lowercase_main_email(self):
        """Test using non-lowercase main email addresses"""
        user = User(
            hrid='louis.vaneau.1829',
            fullname='Louis Vaneau',
            preferred_name='Louis Vaneau',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!'
        )
        user.full_clean()
        user.main_email = 'Louis.Vaneau.1829@polytechnique.org'
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_non_lowercase_alias_email(self):
        """Test using non-lowercase alias email addresses"""
        user = User.objects.create_user(
            hrid='louis.vaneau.1829',
            fullname='Louis Vaneau',
            preferred_name='Louis Vaneau',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!'
        )
        alias = UserAlias(user=user, email='louis.vaneau@polytechnique.org')
        alias.full_clean()
        alias.email = 'Louis.Vaneau@polytechnique.org'
        with self.assertRaises(ValidationError):
            alias.full_clean()
