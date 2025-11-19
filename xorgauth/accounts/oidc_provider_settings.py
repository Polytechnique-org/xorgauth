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
    info_xorg_groups_perm = (
        _("X Groups Perms"),
        _("The list of the X Groups you belong to, suffix with admin if you are an admin")
    )
    info_xorg_study_years = (
        _("Study year"),
        _("The year of your study at the Ecole polytechnique")
    )
    info_xorg_axid = (
        _("AX ID"),
        _("Your identification in AX directory")
    )
    info_xorg_axinfo = (
        _("AX subscription"),
        _("Your subscription information related to AX and the Jaune et la Rouge")
    )

    def scope_xorg_groups(self):
        groups = [membership.group for membership in self.user.groups.all()]
        dic = {
            'x_groups': [g.shortname for g in groups]
        }
        return dic

    def scope_xorg_groups_perm(self):
        groups = []
        for g in self.user.groups.all():
            name = g.group.shortname
            groups.append(name)
            if g.perms == 'admin':
                groups.append(name + '_admin')
        dic = {
            'x_groups_perm': groups
        }
        return dic

    def scope_xorg_study_years(self):
        return {
            'study_years': [self.user.study_year],
        }

    def scope_xorg_axid(self):
        return {
            'axid': self.user.axid,
        }

    def scope_xorg_axinfo(self):
        return {
            'ax_contributor': self.user.ax_contributor,
            'axjr_subscriber': self.user.axjr_subscriber,
        }
