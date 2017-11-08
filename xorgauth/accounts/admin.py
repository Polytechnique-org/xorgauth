# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

from django.contrib import admin

from . import models


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    search_fields = ['hrid', 'display']

    list_display = ['hrid', 'display', 'system']
    list_filter = ['system']


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['hrid', 'main_email', 'fullname', 'preferred_name']

    list_display = ['hrid', 'main_email', 'fullname']
    list_filter = ['roles', 'last_login']


@admin.register(models.UserAlias)
class UserAliasAdmin(admin.ModelAdmin):
    search_fields = ['user__%s' % f for f in UserAdmin.search_fields]

    list_display = ['email', 'user']
    list_select_related = ['user']


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ['shortname'] + ['members__user__%s' % f for f in UserAdmin.search_fields]

    list_display = ['shortname']


@admin.register(models.GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    search_fields = ['group__shortname'] + ['user__%s' % f for f in UserAdmin.search_fields]

    list_display = ['pk', 'group', 'user', 'perms']
    list_filter = ['perms']
