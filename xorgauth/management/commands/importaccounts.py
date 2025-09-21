# -*- coding: utf-8 -*-
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
        is_verbose = int(options['verbosity']) >= 2
        with open(options['jsonfile'][0], 'r') as jsonfd:
            jsondata = json.load(jsonfd)
        if 'accounts' not in jsondata:
            raise CommandError("Unable to find account entries")
        hasher = PBKDF2WrappedSHA1PasswordHasher()
        admin_role = Role.get_admin()
        role_displays = {
            # Alumni
            'x': 'X',
            'master': 'Master',
            'phd': 'PhD',
            'bachelor': 'Bachelor',
            'executive': 'Executive',
            'graduate': 'Graduate Degree',
            'masterspe': 'Master spécialisé',
            # Staff
            'ax': 'AX',
            'fx': 'FX',
            'school': 'School',
            # Other
            'xnet': 'External',
        }
        type_roles = {}
        for rolename, roledisplay in role_displays.items():
            type_roles[rolename], created = Role.objects.get_or_create(hrid=rolename)
            if created:
                if is_verbose:
                    print("Creating role %r (%r)" % (rolename, roledisplay))
                type_roles[rolename].display = roledisplay
                type_roles[rolename].full_clean()
                type_roles[rolename].save()

        groups = {group.shortname: group for group in Group.objects.all()}
        users = {user.hrid: user for user in User.objects.prefetch_related("aliases", "groups", "roles").all()}

        accounts_num = len(jsondata['accounts'])
        for idx_account, account_data in enumerate(jsondata['accounts']):
            # Do not import virtual accounts
            if account_data['type'] == 'virtual':
                continue

            hrid = account_data['hruid']
            try:
                user = users[hrid]
                is_creating_user = False
                if is_verbose:
                    print("Updating user %s (%d/%d)" % (hrid, idx_account + 1, accounts_num))
            except KeyError:
                user = User(hrid=hrid)
                is_creating_user = True
                if is_verbose:
                    print("Creating user %s (%d/%d)" % (hrid, idx_account + 1, accounts_num))

            # Sometimes, display_name is empty. Use the first name or a name
            # from the email address
            if not account_data['display_name']:
                if account_data['firstname']:
                    if is_creating_user and is_verbose:
                        print("... using first name (%r) as display name" % account_data['firstname'])
                    account_data['display_name'] = account_data['firstname']
                else:
                    # This should only happen for external accounts
                    if account_data['type'] != 'xnet':
                        raise CommandError(
                            "No display_name nor firstname for a non-external account: %r" % account_data)

                    display_name = account_data['email'].split('@')[0]
                    if not display_name:
                        raise CommandError(
                            "No display_name nor firstname nor email in account data: %r" % account_data)
                    if is_creating_user and is_verbose:
                        print("... using email user (%r) as display name" % display_name)
                    account_data['display_name'] = display_name

                    # If full name is empty too, use the same display name
                    if not account_data['full_name']:
                        account_data['full_name'] = display_name

            # Update the fields of user, if needed
            user_fields = {
                'fullname': account_data['full_name'],
                'preferred_name': account_data['display_name'],
                'main_email': account_data['email'].lower(),
                'axid': account_data['ax_id'],
                'schoolid': str(account_data['xorg_id']) if account_data['xorg_id'] else None,
                'xorgdb_uid': account_data['uid'],
                'firstname': account_data['firstname'],
                'lastname': account_data['lastname'],
                'sex': account_data['sex'],
                'study_year': account_data['promo'],
                'grad_year': account_data['grad_year'],
            }
            is_user_modified = is_creating_user
            for field_name, new_value in user_fields.items():
                if getattr(user, field_name) != new_value:
                    if not is_creating_user and is_verbose:
                        print("... updating %r because %r is %r, not %r" % (
                            user,
                            field_name,
                            getattr(user, field_name),
                            new_value))
                    is_user_modified = True
                    setattr(user, field_name, new_value)

            if is_creating_user:
                # Do not override the password when updating an existing account
                if account_data['password']:
                    user.password = hasher.encode_sha1_hash(account_data['password'])
                else:
                    user.set_unusable_password()
            elif not user.has_usable_password() and account_data['password']:
                # Allow defining a new password if it was previously unusable.
                # This happens for example when pending accounts get activated
                user.password = hasher.encode_sha1_hash(account_data['password'])
                is_user_modified = True
                if is_verbose:
                    print("... adding password for %r" % user)

            # Validate and save the user only if it has been modified
            if is_user_modified:
                user.full_clean()
                user.save()

            # Import groups
            memberships = {m.group_id: m for m in user.groups.all()}
            for groupname, perms in account_data['groups'].items():
                if groupname not in groups:
                    groups[groupname] = Group.objects.create(shortname=groupname)
                group = groups[groupname]

                # Perform an "update_or_create" on the membership, calling full_clean() also
                changed = False
                if group.pk not in memberships:
                    memberships[group.pk] = GroupMembership(group=group, user=user)
                    changed = True

                membership = memberships[group.pk]
                if membership.perms != perms:
                    membership.perms = perms
                    changed = True

                # Ensure a sane database
                membership.full_clean()
                if changed:
                    membership.save()

            # Import email aliases
            current_user_aliases = set(a.email for a in user.aliases.all())
            for email in account_data['email_source'].keys():
                email = email.lower()
                if email in current_user_aliases:
                    continue
                alias = UserAlias(user=user, email=email)
                alias.full_clean()
                alias.save()

            user_roles = {role.pk for role in user.roles.all()}

            # Add new administrators
            if account_data['is_admin'] and admin_role.pk not in user_roles:
                user.roles.add(admin_role)

            # Import account type into role
            user_type_role = type_roles[account_data['type']]
            if user_type_role.pk not in user_roles:
                user.roles.add(user_type_role)
