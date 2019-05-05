import datetime
import json

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from xorgauth.accounts.models import User


# crypt("secret")
CRYPT_SECRET = (
    '$6$789UF3OtQuQGbJVZ$gorL2XAIfptBDtPObm.NKpO0FDESesSLZyEYDwjPbfbKbkEzLHh0MQ'
    'HCjPL8B3PR.TUaH9eh8OCgQtZDkGAyx/'
)


class ViewTests(TestCase):
    def test_no_sget(self):
        """The view for AX synchronisation only supports POST"""
        c = Client()
        resp = c.get(reverse('sync-ax-data'))
        self.assertEqual(405, resp.status_code)

    def test_no_secret_setting(self):
        """The view for AX synchronisation requires a password in the configuration"""
        c = Client()
        resp = c.post(reverse('sync-ax-data'))
        self.assertEqual(404, resp.status_code)

    @override_settings(AX_SYNC_SECRET_CRYPT=CRYPT_SECRET)
    def test_wrong_password(self):
        c = Client()
        resp = c.post(
            reverse('sync-ax-data'),
            content_type='text/plain',
            data=json.dumps({'secret': 'bad'}),
        )
        self.assertEqual(403, resp.status_code)

    @override_settings(AX_SYNC_SECRET_CRYPT=CRYPT_SECRET)
    def test_bad_json(self):
        c = Client()
        resp = c.post(
            reverse('sync-ax-data'),
            content_type='text/plain',
            data='{"bad":"json"',
        )
        self.assertEqual(400, resp.status_code)

        resp = c.post(
            reverse('sync-ax-data'),
            content_type='text/plain',
            data=json.dumps({'secret': 'secret', 'data': 42}),
        )
        self.assertEqual(400, resp.status_code)

    @override_settings(AX_SYNC_SECRET_CRYPT=CRYPT_SECRET)
    def test_empty_request(self):
        c = Client()
        resp = c.post(
            reverse('sync-ax-data'),
            content_type='text/plain',
            data=json.dumps({'secret': 'secret', 'data': []}),
        )
        self.assertEqual(200, resp.status_code)

    @override_settings(AX_SYNC_SECRET_CRYPT=CRYPT_SECRET)
    def test_sync_nonexisting_user(self):
        c = Client()
        resp = c.post(
            reverse('sync-ax-data'),
            content_type='text/plain',
            data=json.dumps({'secret': 'secret', 'data': [
                {
                    'xorg_id': 'unexisting.user.1942',
                    'af_id': 42,
                    'ax_contributor': True,
                    'axjr_subscribed': True,
                    'last_updated': '1800-01-23',
                },
            ]}),
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, User.objects.filter(hrid='unexisting.user.1942').count())

    @override_settings(AX_SYNC_SECRET_CRYPT=CRYPT_SECRET)
    def test_sync_user(self):
        # Create a user
        user = User.objects.create_user(
            hrid='louis.vaneau.1829',
            main_email='louis.vaneau.1829@polytechnique.org',
            password='Depuis Vaneau!',
            alumnforce_id='1234',
            ax_contributor=False,
        )
        self.assertEqual('1234', user.alumnforce_id)
        self.assertEqual(False, user.ax_contributor)
        self.assertEqual(None, user.axjr_subscriber)
        self.assertEqual(None, user.ax_last_synced)

        # Sync it
        c = Client()
        resp = c.post(
            reverse('sync-ax-data'),
            content_type='text/plain',
            data=json.dumps({'secret': 'secret', 'data': [
                {
                    'xorg_id': 'louis.vaneau.1829',
                    'af_id': 89,
                    'ax_contributor': True,
                    'axjr_subscribed': True,
                    'last_updated': '1830-01-23',
                },
            ]}),
        )
        self.assertEqual(200, resp.status_code)

        # Verify the sync
        user.refresh_from_db()
        self.assertEqual('89', user.alumnforce_id)
        self.assertEqual(True, user.ax_contributor)
        self.assertEqual(True, user.axjr_subscriber)
        self.assertEqual(datetime.date(1830, 1, 23), user.ax_last_synced)

        # Test a partial sync
        resp = c.post(
            reverse('sync-ax-data'),
            content_type='text/plain',
            data=json.dumps({'secret': 'secret', 'data': [
                {
                    'xorg_id': 'louis.vaneau.1829',
                    'af_id': 89,
                    'axjr_subscribed': False,
                },
                {
                    'xorg_id': 'louis.vaneau.1829',
                },
            ]}),
        )
        self.assertEqual(200, resp.status_code)
        user.refresh_from_db()
        self.assertEqual(False, user.axjr_subscriber)
