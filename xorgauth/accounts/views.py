from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from oidc_provider.models import UserConsent, Client


@login_required
def list_consents(request):
    # if a revoke request was done, process it
    revoked_client = None
    error = None
    revoke = request.POST.get('revoke', None)
    if revoke is not None:
        consent = UserConsent.objects.filter(user=request.user, client__client_id=revoke)
        if consent:
            revoked_client = consent[0].client
            consent[0].delete()
        else:
            client = Client.objects.filter(client_id=revoke)
            if client:
                error = "You have no consent for client \"{}\".".format(client[0].name)
            else:
                error = "Unknown client."
    # render the result
    consents = UserConsent.objects.filter(user=request.user)
    return render(request, 'list_consents.html', {
        'error': error,
        'revoked_client': revoked_client,
        'consents': consents
    })
