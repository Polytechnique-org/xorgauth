# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

import hashlib
import re
import sys

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _
from xorgauth.utils.fields import UnboundedCharField


# hmac.compare_digest is only available from Python 3.3
if sys.version_info >= (3, 3):
    from hmac import compare_digest
else:
    def compare_digest(x, y):
        return x == y


class AuthGroupeXClientManager(models.Manager):
    def get_by_url_and_challenge(self, ext_url, gpex_challenge, gpex_pass):
        """Get the client which matches the URL and signed the request"""
        for client in self.all():
            if client.match_return_url(ext_url):
                if client.match_signed_challenge(gpex_challenge, gpex_pass):
                    return client


class AuthGroupeXClient(models.Model):
    privkey = models.CharField(unique=True, max_length=40)
    name = UnboundedCharField(unique=True)
    datafields = UnboundedCharField()
    returnurls = UnboundedCharField()
    last_used = models.DateField(null=True)
    allow_xnet = models.BooleanField(default=False)

    objects = AuthGroupeXClientManager()

    class Meta:
        verbose_name = _("AuthGroupeX client")
        verbose_name_plural = _("AuthGroupeX clients")

    def __str__(self):
        return self.name

    def match_return_url(self, url):
        """Match the given url against the pattern for return URLS"""
        pattern = self.returnurls.strip()
        # PHP's preg_match uses a special character at the beginning and the end
        # of the pattern
        if pattern and pattern[0] == pattern[-1] == '#':
            pattern = pattern[1:-1]
        return re.match(pattern, url)

    def match_signed_challenge(self, gpex_challenge, gpex_pass):
        """Verify that the challenge has been signed with the right key"""
        try:
            computed_pass = hashlib.md5((gpex_challenge + self.privkey).encode('ascii')).hexdigest()
        except UnicodeEncodeError:
            return
        return compare_digest(computed_pass, gpex_pass)

    def add_response_data(self, ext_url_params, user, gpex_challenge, gpex_group):
        """Add user response data into the returned parameters"""
        try:
            hashed_val = ('1' + gpex_challenge + self.privkey).encode('ascii')
        except UnicodeEncodeError:
            return False
        for datafield in self.datafields.split(','):
            val = None
            if datafield == 'perms':
                val = 'admin' if user.is_staff else 'user'
            elif datafield == 'forlife':
                val = user.hrid
            elif datafield == 'prenom':
                val = user.firstname
            elif datafield == 'nom':
                val = user.lastname
            elif datafield == 'sex':
                val = user.sex
            elif datafield == 'matricule_ax':
                val = user.axid
            elif datafield == 'promo':
                val = user.study_year
                while val and not '0' <= val[0] <= '9':
                    val = val[1:]
            elif datafield == 'full_promo':
                val = user.study_year
            elif datafield == 'promo_sortie':
                val = user.grad_year
            elif datafield == 'grpauth' and gpex_group:
                try:
                    grp_membership = user.groups.get(group__shortname=gpex_group)
                    val = grp_membership.perms
                except ObjectDoesNotExist:
                    pass

            if not val:
                val = ''
            ext_url_params[datafield] = val
            try:
                hashed_val += val.encode('utf-8')
            except UnicodeEncodeError:
                return False

        # Sign the values
        auth = hashlib.md5(hashed_val + b'1').hexdigest()
        ext_url_params['auth'] = auth
        return True
