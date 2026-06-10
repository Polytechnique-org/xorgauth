# Upgrade SHA1 passwords nicely
# https://docs.djangoproject.com/en/1.11/topics/auth/passwords/#password-upgrading-without-requiring-a-login
import hashlib
import re

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.utils.encoding import force_bytes


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt=None, iterations=None):
        if salt is None:
            salt = self.salt()
        return super(PBKDF2WrappedSHA1PasswordHasher, self).encode(sha1_hash, salt, iterations)

    def encode(self, password, salt, iterations=None):
        sha1_hash = hashlib.sha1(force_bytes(password)).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)


def parse_sha512_hash(hashed: str) -> dict:
    """
    Extract the components of a $6$ hash (SHA-512 crypt).
    Supported format:
      - $6$salt$hash
      - $6$rounds=N$salt$hash
    """
    pattern = r"^\$6\$(?:rounds=(\d+)\$)?([^$]+)\$(.+)$"
    match = re.match(pattern, hashed)

    if not match:
        raise ValueError("Invalid hash format")

    rounds_str, salt, hash_value = match.groups()
    rounds = int(rounds_str) if rounds_str else 5000  # SHA-512 default

    return {
        "rounds": rounds,
        "salt": salt,
        "hash": hash_value,
    }
