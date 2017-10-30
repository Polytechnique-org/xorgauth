# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

def userinfo(claims, user):
    """Populate claims dict for the given user

    http://django-oidc-provider.readthedocs.io/en/latest/sections/scopesclaims.html
    """
    claims['name'] = user.fullname
    claims['email'] = user.main_email
    return claims
