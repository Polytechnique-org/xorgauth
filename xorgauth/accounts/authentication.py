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
