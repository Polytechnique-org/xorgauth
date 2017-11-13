import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from xorgauth.accounts.hashers import PBKDF2WrappedSHA1PasswordHasher
from xorgauth.accounts.models import User, Group, GroupMembership


class Command(BaseCommand):
    help = "Import a JSON file with accounts data into the database"

    def add_arguments(self, parser):
        parser.add_argument('jsonfile', nargs=1, type=str,
                            help="path to JSON file to load")

    def handle(self, *args, **options):
        with open(options['jsonfile'][0], 'r') as jsonfd:
            jsondata = json.load(jsonfd)
        if 'accounts' not in jsondata:
            raise CommandError("Unable to find account entries")
        hasher = PBKDF2WrappedSHA1PasswordHasher()
        for account_data in jsondata['accounts']:
            hrid = account_data['hruid']
            try:
                user = User.objects.get(hrid=hrid)
            except ObjectDoesNotExist:
                user = User(hrid=hrid)

            user.fullname = account_data['full_name']
            user.preferred_name = account_data['display_name']
            user.main_email = account_data['email']
            user.password = hasher.encode_sha1_hash(account_data['password'])
            user.save()

            # Import groups
            for groupname, perms in account_data['groups'].items():
                group = Group.objects.get_or_create(shortname=groupname)[0]
                GroupMembership.objects.get_or_create(
                    group=group,
                    user=user,
                    perms=perms)
