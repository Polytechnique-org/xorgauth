FROM debian:trixie-slim

ARG XORG_PACKAGE_NAME=xorgauth
ARG XORG_ROOT=/srv/$XORG_PACKAGE_NAME
ARG XORG_VENV=/srv/venv

RUN apt update

# install dependencies
RUN apt install -y python3 uwsgi-plugin-python3 uwsgi

# install build-dependencies
RUN apt install -y python3-setuptools python3-venv make gettext

# copy directory
COPY --exclude=Dockerfile --exclude=docker-compose.yml . $XORG_ROOT

# install and activate venv
RUN python3 -m venv --system-site-packages $XORG_VENV

# build project
ENV DJANGO_ADMIN=$XORG_VENV/bin/django-admin
RUN $XORG_VENV/bin/pip install $XORG_ROOT && make -C $XORG_ROOT

# cleanup apt
RUN apt remove -y make python3-setuptools && apt autoremove -y
RUN rm -rf /var/cache/apt/* /var/lib/apt/lists/*

# install global settings
RUN mkdir /etc/$XORG_PACKAGE_NAME
COPY ./settings.ini /etc/$XORG_PACKAGE_NAME/settings.ini

# uWSGI will listen on this port
EXPOSE 8000

# Add any static environment variables needed by Django or your settings file here:
ENV DJANGO_SETTINGS_MODULE=$XORG_PACKAGE_NAME.settings

# Call collectstatic (customize the following line with the minimal environment variables needed for manage.py to run):
RUN $XORG_VENV/bin/python $XORG_ROOT/manage.py collectstatic --noinput

# Tell uWSGI where to find your wsgi file (change this):
ENV UWSGI_WSGI_FILE=$XORG_ROOT/$XORG_PACKAGE_NAME/wsgi.py

# Base uWSGI configuration (you shouldn't need to change these):
ENV UWSGI_VIRTUALENV=$XORG_VENV UWSGI_MODULE=$XORG_PACKAGE_NAME.wsgi:application UWSGI_HTTP_SOCKET=:8000 UWSGI_MASTER=1 UWSGI_HTTP_AUTO_CHUNKED=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_LAZY_APPS=1 UWSGI_WSGI_ENV_BEHAVIOR=holy

# Number of uWSGI workers and threads per worker (customize as needed):
ENV UWSGI_WORKERS=2 UWSGI_THREADS=4

# uWSGI static file serving configuration (customize or comment out if not needed):
ENV UWSGI_STATIC_MAP="/static/=${XORG_ROOT}/${XORG_PACKAGE_NAME}/static/core/" UWSGI_STATIC_EXPIRES_URI="/static/.*\.[a-f0-9]{12,}\.(css|js|png|jpg|jpeg|gif|ico|woff|ttf|otf|svg|scss|map|txt) 315360000"

ENV UWSGI_ENV="DJANGO_SETTINGS_MODULE=${XORG_PACKAGE_NAME}.settings"
ENV UWSGI_CHDIR=$XORG_ROOT

RUN touch $XORG_ROOT/reload-uwsgi.touchme
ENV UWSGI_TOUCH_RELOAD="${XORG_ROOT}/reload-uwsgi.touchme"

# Start uWSGI
CMD ${XORG_VENV}/bin/python3 $XORG_ROOT/manage.py migrate --noinput; \
    /usr/bin/uwsgi --show-config --plugin /usr/lib/uwsgi/plugins/python3_plugin.so
#CMD $XORG_VENV/bin/python $XORG_ROOT/manage.py runserver --traceback 0.0.0.0:8000
