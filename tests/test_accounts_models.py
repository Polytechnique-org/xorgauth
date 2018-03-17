from django.test import TestCase

from xorgauth.accounts.models import User


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
