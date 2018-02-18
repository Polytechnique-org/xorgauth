from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic.base import RedirectView, TemplateView

from oidc_provider.models import UserConsent, Client

from xorgauth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm


@login_required
def list_consents(request):
    # if a revoke request was done, process it
    revoke = request.POST.get('revoke', None)
    if revoke is not None:
        consent = UserConsent.objects.filter(user=request.user, client__client_id=revoke)
        if consent:
            revoked_client = consent[0].client
            consent[0].delete()
            messages.success(request, "Successfully revoked consent for client \"{}\"".format(revoked_client.name))
        else:
            client = Client.objects.filter(client_id=revoke)
            if client:
                messages.error(request, "You have no consent for client \"{}\".".format(client[0].name))
            else:
                messages.error(request, "Unknown client.")
    # render the result
    consents = UserConsent.objects.filter(user=request.user)
    return render(request, 'list_consents.html', {
        'consents': consents
    })


class IndexView(LoginRequiredMixin, RedirectView):
    pattern_name = 'profile'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def user_has_consents(self):
        """Return true if the logged user has any consent"""
        return UserConsent.objects.filter(user=self.request.user).exists()

    def user_xorg_email(self):
        """Return an email address managed by Polytechnique.org if the user is an alumni"""
        user = self.request.user
        return user.main_email if user.is_x_alumni() else None


class PasswordChangeView(auth_views.PasswordChangeView):
    form_class = PasswordChangeForm


class PasswordResetView(auth_views.PasswordResetView):
    form_class = PasswordResetForm


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    form_class = SetPasswordForm
