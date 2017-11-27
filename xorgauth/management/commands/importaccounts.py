import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from xorgauth.accounts.hashers import PBKDF2WrappedSHA1PasswordHasher
from xorgauth.accounts.models import User, UserAlias, Group, GroupMembership, Role


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
        admin_role = Role.get_admin()
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
            user.axid = account_data['ax_id']
            user.study_year = account_data['promo']
            user.grad_year = account_data['grad_year']
            user.save()
            if account_data['is_admin']:
                user.roles.add(admin_role)
                user.save()

            # Import groups
            for groupname, perms in account_data['groups'].items():
                group = Group.objects.get_or_create(shortname=groupname)[0]
                GroupMembership.objects.get_or_create(
                    group=group,
                    user=user,
                    perms=perms)

            # Import email aliases
            for email in account_data['email_source'].keys():
                try:
                    alias = UserAlias.objects.get(email=email)
                except ObjectDoesNotExist:
                    alias = UserAlias(user=user, email=email)
                    alias.save()
                else:
                    if alias.user != user:
                        raise CommandError("Duplicate email %r" % email)
