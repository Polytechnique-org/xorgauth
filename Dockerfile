ARG DEBIAN_VERSION=trixie
ARG XORG_PACKAGE_NAME=xorgauth
ARG XORG_ROOT=/srv/$XORG_PACKAGE_NAME
ARG XORG_USER=xorg

############################################
##########       Base Image       ##########
############################################

FROM debian:$DEBIAN_VERSION-slim AS base

ARG DEBIAN_VERSION
ARG XORG_ROOT
ARG XORG_USER

# Add backports to install a recent version of django
RUN echo "deb http://deb.debian.org/debian ${DEBIAN_VERSION}-backports main" > /etc/apt/sources.list.d/backports.list

# install dependencies
# install build dependencies
# we use django from debian if it is compatible
# with the package, otherwise, we install another
# version that suits below with pip
RUN \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && \
    apt install -y python3 uwsgi-plugin-python3 uwsgi python3-django python3-passlib python3-mysqldb

# create user
RUN useradd --user-group --system --create-home --home-dir $XORG_ROOT $XORG_USER

ENV DJANGO_SETTINGS_MODULE=$XORG_PACKAGE_NAME.settings

WORKDIR $XORG_ROOT

############################################
########## venv compilation Image ##########
############################################

FROM base AS python-packages

ARG XORG_USER

RUN \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt install -y python3-setuptools python3-venv gettext

# install and activate venv in a separate directory
# allow that venv to use system-installed python3-* packages
# this is useful because in general some python3 modules require compiled binaries,
# which are better maintained within debian packages. E.g. python3-cryptography.
RUN python3 -m venv --system-site-packages venv

# venv commands must take over
ENV PATH=$XORG_ROOT/venv/bin:$PATH

# copy this django app
COPY --chown=$XORG_USER: --exclude=Dockerfile --exclude=docker-compose.yml --exclude=*.ini . app

# install deps
RUN pip install ./app

# build
RUN django-admin compilemessages

# collect to app/static
RUN django-admin collectstatic --noinput

############################################
##########      App Image      ##########
############################################

FROM base

ARG XORG_PACKAGE_NAME
ARG XORG_ROOT
ARG XORG_USER
COPY --from=python-packages $XORG_ROOT $XORG_ROOT

USER $XORG_USER
# venv commands must take over
ENV PATH=${XORG_ROOT}/venv/bin:$PATH

# now everything we do is from app
WORKDIR $XORG_ROOT/app

# touch reload, usefull for debugging
RUN touch reload-uwsgi.touchme
ENV UWSGI_TOUCH_RELOAD=$XORG_ROOT/app/reload-uwsgi.touchme

USER root
# install global settings
RUN mkdir /etc/$XORG_PACKAGE_NAME
COPY ./settings.ini /etc/$XORG_PACKAGE_NAME/settings.ini

# uWSGI will listen on this port
EXPOSE 8000

# Switch back to user
USER $XORG_USER

# Tell uWSGI where to find your wsgi file (change this):
ENV UWSGI_WSGI_FILE=$XORG_ROOT/app/$XORG_PACKAGE_NAME/wsgi.py

# Base uWSGI configuration (you shouldn't need to change these):
ENV UWSGI_VIRTUALENV=$XORG_ROOT/venv UWSGI_MODULE=$XORG_PACKAGE_NAME.wsgi:application UWSGI_HTTP_SOCKET=:8000 UWSGI_MASTER=1 UWSGI_HTTP_AUTO_CHUNKED=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_LAZY_APPS=1 UWSGI_WSGI_ENV_BEHAVIOR=holy

# Number of uWSGI workers and threads per worker (customize as needed):
ENV UWSGI_WORKERS=2 UWSGI_THREADS=4

# uWSGI static file serving configuration (customize or comment out if not needed):
ENV UWSGI_STATIC_MAP="/static/=${XORG_ROOT}/app/static/" UWSGI_STATIC_EXPIRES_URI="/static/.*\.[a-f0-9]{12,}\.(css|js|png|jpg|jpeg|gif|ico|woff|ttf|otf|svg|scss|map|txt) 315360000"

ENV UWSGI_ENV="DJANGO_SETTINGS_MODULE=${XORG_PACKAGE_NAME}.settings"
ENV UWSGI_CHDIR=$XORG_ROOT

# Deny invalid hosts before they get to Django (uncomment and change to your hostname(s)):
ENV UWSGI_ROUTE_HOST="^(?!data\.m4x\.org$) break:400"

# Start uWSGI using system-installed package
SHELL ["/bin/bash", "-c"]
CMD django-admin migrate --noinput && \
    /usr/bin/uwsgi --show-config --plugin /usr/lib/uwsgi/plugins/python3_plugin.so
