from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from oidc_provider.models import UserConsent, Client


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


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
