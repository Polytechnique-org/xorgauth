# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

from django.db import models
from xorgauth.utils.fields import UnboundedCharField
from django.utils.translation import ugettext_lazy as _


class AuthGroupeXClient(models.Model):
    privkey = models.CharField(unique=True, max_length=40)
    name = UnboundedCharField(unique=True)
    datafields = UnboundedCharField()
    returnurls = UnboundedCharField()
    last_used = models.DateField(null=True)
    allow_xnet = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("AuthGroupeX client")
        verbose_name_plural = _("AuthGroupeX clients")
