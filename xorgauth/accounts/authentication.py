from django.contrib.auth.backends import ModelBackend

from xorgauth.accounts.models import User


class XorgBackend(ModelBackend):
    """This backend handles authentication via any mail alias

    It inherits from django's default backend to keep all other behavior,
    just overriding the user search given an hrid or email
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = User.objects.get_for_login(username)
        if user is None:
            return

        # we now have a candidate user
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
