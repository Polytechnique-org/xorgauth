import json
import os.path

from django.conf import settings
from django.views.generic import TemplateView


class RelyingParty(TemplateView):
    template_name = 'relying-party-test.html'

    def get_context_data(self, **kwargs):
        kwargs = super(RelyingParty, self).get_context_data(**kwargs)

        # Make the base URL accessible to the template
        kwargs['base_url'] = self.request.build_absolute_uri('/')

        # Show some useful accounts in development mode
        if settings.DEBUG:
            with open(os.path.join(settings.BASE_DIR, 'scripts', 'dev_data.json')) as fd:
                json_data = json.load(fd)
                kwargs['dev_accounts'] = json_data['accounts']
        return kwargs
