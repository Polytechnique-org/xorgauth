# -*- coding: utf-8 -*-
# Copyright (c) Polytechnique.org
# This code is distributed under the Affero General Public License version 3
import crypt
import sys

from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string

from . import models


class GoogleAppsPasswordValidator(object):
    """Update the Google Apps password when a user changes her password"""

    def validate(self, password, user=None):
        return

    def password_changed(self, raw_password, user):
        # Hash the password in a way compatible with Google Apps: crypt with $6
        if sys.version_info >= (3,):
            password = crypt.crypt(raw_password, salt=crypt.METHOD_SHA512)
        else:
            password = crypt.crypt(raw_password.encode('utf-8'), '$6$' + get_random_string(16))
        try:
            user.gapps_password.password = password
        except ObjectDoesNotExist:
            models.GoogleAppsPassword.objects.create(user=user, password=password)
        else:
            user.gapps_password.save()
