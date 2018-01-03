"""
Django settings for xorgauth project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
from __future__ import unicode_literals

import getconf
import os

from django.core.exceptions import ImproperlyConfigured


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

config = getconf.ConfigGetter('xorgauth', [
    '/etc/xorgauth/*.ini',
    os.path.join(BASE_DIR, 'local_settings.ini'),
])

APPMODE = config.getstr('app.mode', 'dev')
assert APPMODE in ('dev', 'dist', 'prod'), "Invalid application mode %s" % APPMODE

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.getstr('app.secret_key', 'Dev only!!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.getbool('app.debug', APPMODE == 'dev')

if config.getstr('site.admin_mail'):
    ADMINS = (
        ("XorgAuth admins", config.getstr('site.admin_mail')),
    )

ALLOWED_HOSTS = config.getlist('site.allowed_hosts', [])


# Application definition

INSTALLED_APPS = [
    'xorgauth.accounts.apps.AccountsConfig',
    'xorgauth',
    'xorgauth.authgroupex',
    'xorgauth.relying_party_test',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'oidc_provider',
    'zxcvbn_password',
    'bootstrap3',
]

AUTHENTICATION_BACKENDS = [
    'xorgauth.accounts.authentication.XorgBackend'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'xorgauth.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'xorgauth.wsgi.application'


AUTH_USER_MODEL = 'accounts.User'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

_ENGINE_MAP = {
    'sqlite': 'django.db.backends.sqlite3',
    'mysql': 'django.db.backends.mysql',
    'postgresql': 'django.db.backends.postgresql_psycopg2',
}
_engine = config.getstr('db.engine', 'sqlite')
if _engine not in _ENGINE_MAP:
    raise ImproperlyConfigured(
        "DB engine %s is unknown; please choose from %s" %
        (_engine, ', '.join(sorted(_ENGINE_MAP.keys())))
    )
if _engine == 'sqlite':
    if APPMODE == 'dev':
        _default_db_name = os.path.join(BASE_DIR, 'dev', 'db.sqlite')
    else:
        _default_db_name = '/var/lib/xorgauth/db.sqlite'
else:
    _default_db_name = 'xorgauth'

DATABASES = {
    'default': {
        'ENGINE': _ENGINE_MAP[_engine],
        'NAME': config.getstr('db.name', _default_db_name),
        'USER': config.getstr('db.user'),
        'PASSWORD': config.getstr('db.password'),
        'HOST': config.getstr('db.host', 'localhost'),
        'PORT': config.getstr('db.port'),
    },
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'zxcvbn_password.ZXCVBNValidator',
        'OPTIONS': {
            'min_score': 3,
            'user_attributes':
                ('hrid', 'main_email', 'fullname', 'preferred_name',
                    'firstname', 'lastname', 'grad_year', 'schoolid',
                    'study_year')
        }
    },
]

# Password hashers
# https://docs.djangoproject.com/en/1.11/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'xorgauth.accounts.hashers.PBKDF2WrappedSHA1PasswordHasher',
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/
from django.utils.translation import ugettext_lazy as _
LANGUAGES = (
    ('en', _('English')),
    ('fr', _('French')),
    ('vi', _('Vietnamese')),
    ('zh-tw', _('Chinese traditional')),
    ('zh-cn', _('Chinese simplified')),
)
LANGUAGE_CODE = 'vi'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'third_party', 'zxcvbn_password', 'locale'),
]

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# django-oidc-provider configuration
OIDC_USERINFO = 'xorgauth.accounts.oidc_provider_settings.userinfo'
OIDC_EXTRA_SCOPE_CLAIMS = 'xorgauth.accounts.oidc_provider_settings.XorgScopeClaims'
OIDC_IDTOKEN_SUB_GENERATOR = 'xorgauth.accounts.oidc_provider_settings.user_sub_generator'

# reset user forgotten password
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # During development only

EMAIL_HOST = 'ssl.polytechnique.org'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'quoc-anh.tran.1962@polytechnique.org'
EMAIL_HOST_PASSWORD = 'BnQF0-vOj'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'TestSite Team <noreply@example.com>'