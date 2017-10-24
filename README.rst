xorgauth
========

.. image:: https://secure.travis-ci.org/Polytechnique-org/xorgauth.png?branch=master
    :target: http://travis-ci.org/Polytechnique-org/xorgauth/

.. image:: https://img.shields.io/pypi/v/xorgauth.svg
    :target: https://pypi.python.org/pypi/xorgauth/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/xorgauth.svg
    :target: https://pypi.python.org/pypi/xorgauth/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/wheel/xorgauth.svg
    :target: https://pypi.python.org/pypi/xorgauth/
    :alt: Wheel status

.. image:: https://img.shields.io/pypi/l/xorgauth.svg
    :target: https://pypi.python.org/pypi/xorgauth/
    :alt: License

xorgauth handles authentication / authorization for Polytechnique.org-related services.


.. note::

    This is currently a work in progress.


Features (planned)
------------------

* Login with any alumni email address
* OpenID Connect v1.0 provider
* Legacy auth-groupe-x authentication provider
* Multiple authentication levels (cookie, password, two-factor)


Notes
-----

* Use https://testpypi.python.org/pypi/django-zxcvbn-password/2.0.0 for password entry
* As a provider, return a list of "group access levels" + "role-based permissions"

* Run the following commands in order to setup a development environment::

    make update
    make createdb
    python manage.py createsuperuser --fullname me --hrid me --preferred_name me --main_email me@localhost.localdomain
    python manage.py runserver
    # Go to http://127.0.0.1:8000/admin/ to configure django-oidc-provider

* Documentation:
  - https://django-oidc-provider.readthedocs.io/ for the identity provider
  - https://mozilla-django-oidc.readthedocs.io/ in order to configure a test relying party (client)
