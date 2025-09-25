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


:note:
    This is currently a work in progress.


Features (planned)
------------------

* Login with any alumni email address
* OpenID Connect v1.0 provider
* Legacy auth-groupe-x authentication provider
* Multiple authentication levels (cookie, password, two-factor)


Configuring a development environment
-------------------------------------

Run the following commands in order to setup a development environment on a local computer::

    make update
    make createdb
    make
    python manage.py createsuperuser --fullname me --hrid me --preferred_name me --main_email me@localhost.localdomain
    python manage.py importaccounts scripts/dev_data.json
    python manage.py importauthgroupex scripts/dev_data.json
    python manage.py runserver
    # Go to http://127.0.0.1:8000/admin/ to configure django-oidc-provider

In such a development environment, in order to use the test relying party:

* run ``python manage.py shell`` and add a client:

  .. code-block:: python

      from oidc_provider.models import Client, ResponseType
      c = Client(name='Test RP', client_id='123456', redirect_uris=['http://localhost:8000/test-relying-party/','http://127.0.0.1:8000/test-relying-party/'])
      c.save()
      c.response_types.add(ResponseType.objects.get(value='id_token token'))

* run ``python manage.py runserver 8000``
* open http://localhost:8000/test-relying-party/ in a web browser and click on the log in button


Configuring a production environment
------------------------------------

On Debian, configure a web server (Apache, ngninx, etc.) to serve Django applications (using uwsgi, mod_wsgi, etc.) by reading the documents relevant to these systems. It is a good idea to use a dedicated Python virtual environment.

In order to configure the production application, copy ``example_settings.ini`` to ``local_settings.ini`` and edit this new file accordingly (DNS hostname, admin email address, database credentials, etc.). It is also possible to use environment variables to give some settings to the Django application (thanks to getconf_). It is then possible to initialize the database with::

    make createdb

.. _getconf: https://pypi.python.org/pypi/getconf/

Here are instructions specific to xorgauth application for upgrading::

    make update
    python manage.py migrate
    python manage.py collectstatic
    # Recompile the translation files
    make


Building and using a docker/podman image
----------------------------------------

This commands work using either podman or docker.

## For development

To build the image::

    podman build --file Dockerfile --tag xorgauth

One can create, start, and attach to a container for development (ctrl-c to kill it), that will bind-mount current directory in place of the app in the image::

    podman run --interactive --tty --replace --name xorgauth_dev --mount type=bind,src=.,dst=/srv/xorgauth/app --publish 8000:8000 xorgauth:latest

Make changes to the code in the current directory, and reload the application quickly::

    touch reload-uwsgi.touchme

which is way quicker than restarting the container.

One can also get a shell in the container::

    podman exec -it xorgauth_dev /bin/bash
    $> python manage.py importaccounts scripts/dev_data.json

## For production

A production container would just be::

    podman create --name xorgauth_prod --publish 8000:8202 xorgauth:latest

To start it, just::

    podman start xorgauth_prod

To see the logs::

    podman logs --follow xorgauth_prod

One can kill, restart, etc...


Notes
-----

* After adding a new translation tag in an html template, you can recreate the translation file with the command ``make poupdate`` (the blocks with "fuzzy" are ignored)
* Before running the ``collectstatic`` command, make sure to manually add all necessary static files to the project. In particular, the JavaScript and CSS dependencies must be downloaded and placed in the ``xorgauth/static/`` directory of this project; **remember to update them regularly**
* Use https://testpypi.python.org/pypi/django-zxcvbn-password/2.0.0 for password entry
* As a provider, return a list of "group access levels" + "role-based permissions"

* Documentation:
    - https://django-oidc-provider.readthedocs.io/ for the identity provider
    - https://mozilla-django-oidc.readthedocs.io/ in order to configure a test relying party (client)
