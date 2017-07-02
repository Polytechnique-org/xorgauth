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
