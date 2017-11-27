# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

from django.utils.translation import ugettext_lazy as _
from oidc_provider.lib.claims import ScopeClaims


def userinfo(claims, user):
    """Populate claims dict for the given user

    http://django-oidc-provider.readthedocs.io/en/latest/sections/scopesclaims.html
    """
    claims['name'] = user.fullname
    claims['email'] = user.main_email
    return claims


def user_sub_generator(user):
    """Use the human-readable ID of a user as the "sub" claim in userinfo scope
    """
    return user.hrid


class XorgScopeClaims(ScopeClaims):
    info_xorg_groups = (
        _("X Groups"),
        _("The list of the X Groups you belong to")
    )

    def scope_xorg_groups(self):
        groups = [membership.group for membership in self.user.groups.all()]
        dic = {
            'x_groups': [g.shortname for g in groups]
        }
        return dic
