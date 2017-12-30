from django.contrib.auth import forms as auth_forms
from django.utils.translation import gettext, gettext_lazy as _
from zxcvbn_password.fields import PasswordField, PasswordConfirmationField

class SetPasswordForm(auth_forms.SetPasswordForm):
    new_password1 = PasswordField(
        label=_("New password"),
        strip=False,
        )
    new_password2 = PasswordConfirmationField(
        confirm_with='new_password1',
        label=_("New password confirmation"),
        strip=False,
        )

class PasswordChangeForm(SetPasswordForm, auth_forms.PasswordChangeForm):
    pass
