# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3

from django.core.exceptions import ObjectDoesNotExist
from passlib.hash import sha512_crypt

from . import models


class GoogleAppsPasswordValidator(object):
    """Update the Google Apps password when a user changes her password"""

    def validate(self, password, user=None):
        return

    def password_changed(self, raw_password, user):
        # Hash the password in a way compatible with Google Apps: crypt with $6
        password = sha512_crypt.using().hash(raw_password)
        try:
            user.gapps_password.password = password
        except ObjectDoesNotExist:
            models.GoogleAppsPassword.objects.create(user=user, password=password)
        else:
            user.gapps_password.save()
