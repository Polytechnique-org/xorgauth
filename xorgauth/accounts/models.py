# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

import uuid

from django.contrib.auth import base_user
from django.db import models

from django.utils.translation import ugettext_lazy as _

from xorgauth.utils.fields import UnboundedCharField


ADMIN_ROLE_HRID = 'admin'


class Role(models.Model):
    system = models.BooleanField(_("system role"), default=False, editable=False)
    hrid = models.SlugField(_("human-readable identifier"), unique=True)
    display = UnboundedCharField(_("display name"), unique=True)

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")

    def __str__(self):
        return self.hrid

    @classmethod
    def get_admin(cls):
        return cls.objects.get(hrid=ADMIN_ROLE_HRID)


class UserManager(base_user.BaseUserManager):
    def create_user(self, hrid, main_email, password, **extra_fields):
        main_email = self.normalize_email(main_email)
        user = self.model(hrid=hrid, main_email=main_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, hrid, main_email, password, **extra_fields):
        main_email = self.normalize_email(main_email)
        user = self.model(hrid=hrid, main_email=main_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        user.roles.add(Role.get_admin())
        user.save(using=self._db)
        return user


class User(base_user.AbstractBaseUser):
    uid = models.UUIDField("UUID", default=uuid.uuid4, editable=False)
    hrid = models.SlugField(_("username"), unique=True)
    fullname = UnboundedCharField(_("full name"), help_text=_("Name to display to other users"))
    preferred_name = UnboundedCharField(_("preferred name"), help_text=_("Name used when addressing the user"))
    main_email = models.EmailField(_("email"), unique=True)
    roles = models.ManyToManyField(Role, related_name='members', verbose_name=_("roles"))
    axid = UnboundedCharField(_("AX ID"), null=True, help_text=_("Identification in AX directory"))
    study_year = UnboundedCharField(_("study year"), null=True, help_text=_(
        "Kind and main year of the study ('X1829' means 'entered the school in 1829 " +
        "but 'M2005' means 'graduated in 2005')"))
    grad_year = models.IntegerField(_("graduation year"), null=True, help_text=_("Year of the graduation"))

    objects = UserManager()

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

    @property
    def is_staff(self):
        """Staff members are defined by the admin role"""
        return self.roles.filter(hrid=ADMIN_ROLE_HRID).count() > 0

    @property
    def email(self):
        """Hack to work around a bug in django-oidc-provider"""
        field_name = self.get_email_field_name()
        return getattr(self, field_name)

    def has_module_perms(self, app_label):
        # staff members have every right
        if self.is_staff:
            return True
        # FIXME implement permissions for other user kinds
        return False

    def has_perm(self, perm, obj=None):
        # staff members have every right
        if self.is_staff:
            return True
        # FIXME implement permissions for other user kinds
        return False


class UserAlias(models.Model):
    """Alias login"""
    user = models.ForeignKey(User, related_name='aliases', verbose_name=_("user"))
    email = models.EmailField(_("email alias"), unique=True)

    class Meta:
        verbose_name = _("user alias")
        verbose_name_plural = _("user aliases")

    def __str__(self):
        return self.email


class Group(models.Model):
    """Group of people"""
    shortname = models.SlugField(_("short name"), unique=True)

    class Meta:
        verbose_name = _("group")
        verbose_name_plural = _("groups")

    def __str__(self):
        return self.shortname


class GroupMembership(models.Model):
    """Relationship between a user and a group"""
    MEMBERSHIP_PERMS = (
        ('member', _('member')),
        ('admin', _('administrator')),
    )
    group = models.ForeignKey(Group, related_name='members', verbose_name=_("group"))
    user = models.ForeignKey(User, related_name='groups', verbose_name=_("member"))
    perms = models.SlugField(choices=MEMBERSHIP_PERMS)

    class Meta:
        unique_together = ('group', 'user',)
