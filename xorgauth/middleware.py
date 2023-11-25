# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3


class AXOIDCFixerMiddleware:
    """
    Middleware used for fixing invalid AX OIDC requests.

    Those requests suffer from an invalid level of URL encoding: parameters are
    sent as `&amp;client_id=123456` instead of `&client_id=123456`.

    Remove those extra &amp;
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.path.startswith("/openid/authorize")
            and request.method == "GET"
            and "amp;client_id" in request.GET
        ):
            new_get = request.GET.copy()

            for key in request.GET.keys():
                if key.startswith("amp;"):
                    good_key = key[4:]
                    # A key might occur several times, copy all its values.
                    for value in new_get.pop(key):
                        new_get.appendlist(good_key, value)
            request.GET = new_get
        return self.get_response(request)
