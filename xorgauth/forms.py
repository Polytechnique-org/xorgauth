from django.contrib.auth import forms as auth_forms
from zxcvbn_password.fields import PasswordField, PasswordConfirmationField

class SetPasswordForm(auth_forms.SetPasswordForm):
    new_password1 = PasswordField()
    new_password2 = PasswordConfirmationField(confirm_with='new_password1')

class PasswordChangeForm(SetPasswordForm, auth_forms.PasswordChangeForm):
    pass
