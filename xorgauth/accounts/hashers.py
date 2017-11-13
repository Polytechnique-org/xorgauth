# Upgrade SHA1 passwords nicely
# https://docs.djangoproject.com/en/1.11/topics/auth/passwords/#password-upgrading-without-requiring-a-login
import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.utils.encoding import force_bytes


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    algorithm = 'pbkdf2_wrapped_sha1'

    def encode_sha1_hash(self, sha1_hash, salt=None, iterations=None):
        if salt is None:
            salt = self.salt()
        return super(PBKDF2WrappedSHA1PasswordHasher, self).encode(
            sha1_hash, salt, iterations)

    def encode(self, password, salt, iterations=None):
        sha1_hash = hashlib.sha1(force_bytes(password)).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)
