# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

import re

from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, QueryDict
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View

from .models import AuthGroupeXClient


class AuthGroupeXLoginView(auth_views.LoginView):
    template_name = 'authgroupex/login.html'

    def get_context_data(self, **kwargs):
        context = super(AuthGroupeXLoginView, self).get_context_data(**kwargs)
        # Find the external URL in next value
        next_value = context.get('next', '')
        if '?' in next_value:
            query_params = QueryDict(next_value.split('?', 1)[1])
            ext_url = query_params.get('url', '')
            # make exturl printable
            if len(ext_url) >= 120:
                ext_url = ext_url[120:] + '...'
            context['ext_url'] = ext_url
        return context


class AuthGroupeXView(LoginRequiredMixin, View):
    def get_login_url(self):
        return reverse('auth-groupex-login')

    def get(self, request, *args, **kwargs):
        ext_url = request.GET.get('url')
        php_session = request.GET.get('session')
        gpex_challenge = request.GET.get('challenge')
        gpex_pass = request.GET.get('pass')
        gpex_group = request.GET.get('group')
        if not ext_url:
            return HttpResponseBadRequest('error: missing url')
        if not gpex_challenge:
            return HttpResponseBadRequest('error: missing challenge')
        if not gpex_pass:
            return HttpResponseBadRequest('error: missing gpex_pass')

        # Split the external URL parameters
        if '?' in ext_url:
            ext_url, params = ext_url.split('?', 1)
            ext_url_params = QueryDict(params, mutable=True)
        else:
            ext_url_params = QueryDict(mutable=True)

        # Normalize the return URL
        if not re.match(r'^(http|https)://', ext_url):
            ext_url = 'http://' + ext_url

        # Get the client which signed the request
        client = AuthGroupeXClient.objects.get_by_url_and_challenge(
            ext_url, gpex_challenge, gpex_pass)
        if not client:
            return HttpResponseBadRequest('error: unknown client URL or bad challenge signature')

        # Update the last used date
        client.last_used = timezone.now()
        client.save()

        # If the client does not allow external accounts, restrict access accordingly
        if not client.allow_xnet:
            # if user.roles.filter(hrid='xnet').exists():
            if not request.user.is_x_alumni():
                return HttpResponseForbidden("The requested site is restricted to Ecole polytechnique's alumni")

        # Prepare the response data
        if not client.add_response_data(ext_url_params, request.user, gpex_challenge, gpex_group):
            return HttpResponseBadRequest("error: something wrong happened")

        # Add session as PHPSESSID into ext_url parameters
        if php_session:
            ext_url_params['PHPSESSID'] = php_session

        return HttpResponseRedirect('%s?%s' % (ext_url, ext_url_params.urlencode()))


class AuthGroupeXLogoutView(View):
    def get(self, request, *args, **kwargs):
        ext_url = request.GET.get('url')
        php_session = request.GET.get('session')
        gpex_challenge = request.GET.get('challenge')
        gpex_pass = request.GET.get('pass')
        if not ext_url:
            return HttpResponseBadRequest('error: missing url')
        if not gpex_challenge:
            return HttpResponseBadRequest('error: missing challenge')
        if not gpex_pass:
            return HttpResponseBadRequest('error: missing gpex_pass')

        # Split the external URL parameters
        if '?' in ext_url:
            ext_url, params = ext_url.split('?', 1)
            ext_url_params = QueryDict(params, mutable=True)
        else:
            ext_url_params = QueryDict(mutable=True)

        # Normalize the return URL
        if not re.match(r'^(http|https)://', ext_url):
            ext_url = 'http://' + ext_url

        # Get the client which signed the request
        client = AuthGroupeXClient.objects.get_by_url_and_challenge(
            ext_url, gpex_challenge, gpex_pass)
        if not client:
            return HttpResponseBadRequest('error: unknown client URL or bad challenge signature')

        # Log out the user and redirect to the redirection URL
        logout(request)

        # Add session as PHPSESSID into ext_url parameters
        if php_session:
            ext_url_params['PHPSESSID'] = php_session

        ext_url_params_str = ext_url_params.urlencode()
        if ext_url_params_str:
            ext_url += '?' + ext_url_params_str
        return HttpResponseRedirect(ext_url)
