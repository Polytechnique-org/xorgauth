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
    info_xorg_study_year = (
        _("Study year"),
        _("The year of your study at the Ecole polytechnique")
    )
    info_xorg_axid = (
        _("AX ID"),
        _("Your identification in AX directory")
    )

    def scope_xorg_groups(self):
        groups = [membership.group for membership in self.user.groups.all()]
        dic = {
            'x_groups': [g.shortname for g in groups]
        }
        return dic

    def scope_xorg_study_year(self):
        return {
            'study_year': self.user.study_year,
            'grad_year': self.user.grad_year,
        }

    def scope_xorg_axid(self):
        return {
            'axid': self.user.axid,
        }
