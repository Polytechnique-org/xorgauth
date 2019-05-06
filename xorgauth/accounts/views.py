import crypt
import json
import hmac

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from django.views.generic.base import RedirectView, TemplateView, View

from oidc_provider.models import UserConsent, Client

from xorgauth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm

from .models import User


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


class SyncAxData(View):
    def post(self, request, *args, **kwargs):
        """Receive some data for syncing"""
        # Do not do anything if no secret has been defined
        if not settings.AX_SYNC_SECRET_CRYPT:
            raise Http404("AX sync has not been configured")

        try:
            data = json.loads(request.body.decode('ascii'))
        except ValueError:
            return HttpResponseBadRequest("Unable to load request")

        # data['secret'] is a password for authenticating the data provider
        digest = crypt.crypt(data.get('secret'), settings.AX_SYNC_SECRET_CRYPT)
        if not hmac.compare_digest(digest, settings.AX_SYNC_SECRET_CRYPT):
            return HttpResponseForbidden("Unauthenticated")

        # Mapping from User model to value in JSON request
        field_mapping = (
            ('alumnforce_id', 'af_id'),
            ('ax_contributor', 'ax_contributor'),
            ('axjr_subscriber', 'axjr_subscribed'),
            ('ax_last_synced', 'last_updated'),
        )
        try:
            for account_data in data['data']:
                try:
                    user = User.objects.get(hrid=account_data['xorg_id'])
                except User.DoesNotExist:
                    # Silently skip users that do not exist
                    # If they are created, they will be synced the next time a
                    # synchronisation request is sent to xorgauth.
                    continue

                # Change the account and commit the object only if there were some changes
                changed = False
                for model_field, json_field in field_mapping:
                    if json_field not in account_data:
                        continue
                    new_value = account_data[json_field]
                    if getattr(user, model_field) != new_value:
                        setattr(user, model_field, new_value)
                        changed = True
                if changed:
                    user.save()
        except (KeyError, TypeError, ValueError):
            return HttpResponseBadRequest("Unable to parse the request")
        return HttpResponse("Sync OK", status=200)


if settings.MAINTENANCE:
    # Disable the forms in maintenance mode

    class PasswordChangeView(LoginRequiredMixin, TemplateView):
        template_name = 'registration/password_change_form.html'

    class PasswordResetView(TemplateView):
        template_name = 'registration/password_reset_form.html'

    class PasswordResetConfirmView(TemplateView):
        template_name = 'registration/password_reset_confirm.html'

else:

    class PasswordChangeView(auth_views.PasswordChangeView):
        form_class = PasswordChangeForm

    class PasswordResetView(auth_views.PasswordResetView):
        form_class = PasswordResetForm

    class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
        form_class = SetPasswordForm
