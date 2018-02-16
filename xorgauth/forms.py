from django.contrib.auth import forms as auth_forms
import django.forms
from django.utils.translation import gettext_lazy as _
from zxcvbn_password.fields import PasswordField, PasswordConfirmationField

from xorgauth.accounts.models import User


class AuthenticationForm(auth_forms.AuthenticationForm):
    # override username label
    username = auth_forms.UsernameField(
        label=_("User name or email address"),
        widget=django.forms.TextInput(attrs={'placeholder': _('firstname.lastname.gradyear')}),
        max_length=254)


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


class PasswordResetFrom(auth_forms.PasswordResetForm):
    """Override PasswordResetForm from django.contrib.auth in order to allow
    any user alias when recovering a lost password
    """
    email = auth_forms.UsernameField(
        label=_("User name or email address"),
        widget=django.forms.TextInput(attrs={'placeholder': _('firstname.lastname.gradyear')}),
        max_length=254)

    def clean(self):
        cleaned_data = super(PasswordResetFrom, self).clean()
        # Transform a login or an email alias to a main email address
        if 'email' not in cleaned_data:
            return
        email = cleaned_data['email']
        user = User.objects.get_for_login(email, True)
        if user is None:
            self._errors['email'] = self.error_class([_("Unknown user account")])
            del cleaned_data['email']
            return cleaned_data

        cleaned_data['user'] = user
        cleaned_data['email'] = user.main_email

    def get_users(self, email):
        # get_users is only called when self.cleaned_data has been populated,
        # otherwise there is an internal (Django) error
        assert self.cleaned_data["email"] == email
        assert self.cleaned_data['user'] is not None
        return [self.cleaned_data['user']]
