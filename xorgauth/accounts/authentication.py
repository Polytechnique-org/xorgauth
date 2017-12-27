from django.contrib.auth.backends import ModelBackend

from xorgauth.accounts.models import User, UserAlias


class XorgBackend(ModelBackend):
    """This backend handles authentication via any mail alias

    It inherits from django's default backend to keep all other behavior,
    just overriding the user search given an hrid or email
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if '@' not in username:
            # try to login with hrid
            try:
                user = User.objects.get(hrid=username)
            except User.DoesNotExist:
                # if the username is "firstname.lastname", try builing an hrid
                user = None
                hrid_prefix = username + '.'
                for possible_user in User.objects.filter(hrid__startswith=hrid_prefix):
                    # Sanity check
                    if not possible_user.hrid.startswith(hrid_prefix):
                        return None
                    # No dot in the last part
                    if '.' in possible_user.hrid[len(hrid_prefix):]:
                        continue
                    # Several users share the same firstname.lastname prefix,
                    # refuse to log in.
                    if user is not None:
                        return None
                    user = possible_user
                # Return nothing if no user has been found
                if user is None:
                    return None
        else:
            # try to login with email
            try:
                # try main email
                user = User.objects.get(main_email=username)
            except User.DoesNotExist:
                # try aliases
                try:
                    user = UserAlias.objects.get(email=username).user
                except UserAlias.DoesNotExist:
                    return None
        # we now have a candidate user
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
