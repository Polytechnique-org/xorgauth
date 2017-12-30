# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

from django.contrib import admin

from . import models


@admin.register(models.AuthGroupeXClient)
class AuthGroupeXClientAdmin(admin.ModelAdmin):
    search_fields = ['name', 'return_urls', 'last_used', 'data_fields', 'allow_xnet']

    list_display = ['name', 'return_urls', 'last_used', 'data_fields', 'allow_xnet']
