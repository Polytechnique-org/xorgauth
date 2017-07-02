# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

import uuid

from django.contrib.auth import base_user
from django.db import models

from django.utils.translation import ugettext_lazy as _

from xorgauth.utils.fields import UnboundedCharField


class Role(models.Model):
    system = models.BooleanField(_("system role"), default=False, editable=False)
    hrid = models.SlugField(_("human-readable identifier"), unique=True)
    display = UnboundedCharField(_("display name"), unique=True)

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")

    def __str__(self):
        return self.hrid


class User(base_user.AbstractBaseUser):
    uid = models.UUIDField("UUID", default=uuid.uuid4, editable=False)
    hrid = models.SlugField(_("human-readable identifier"), unique=True)
    fullname = UnboundedCharField(_("full name"), help_text=_("Name to display to other users"))
    preferred_name = UnboundedCharField(_("preferred name"), help_text=_("Name used when addressing the user"))
    main_email = models.EmailField(_("email"), unique=True)
    roles = models.ManyToManyField(Role, related_name='members', verbose_name=_("roles"))

    class Meta:
        verbose_name = _("user account")
        verbose_name_plural = _("user accounts")

    # base_user.AbstractBaseUser bridge

    EMAIL_FIELD = 'main_email'
    USERNAME_FIELD = 'hrid'
    REQUIRED_FIELDS = ['fullname', 'preferred_name', 'main_email']

    def get_username(self):
        return self.hrid

    def get_full_name(self):
        return self.fullname

    def get_short_name(self):
        return self.preferred_name


class UserAlias(models.Model):
    """Alias login"""
    user = models.ForeignKey(User, related_name='aliases', verbose_name=_("user"))
    email = models.EmailField(_("email alias"), unique=True)

    class Meta:
        verbose_name = _("user alias")
        verbose_name_plural = _("user aliases")

    def __str__(self):
        return self.email


