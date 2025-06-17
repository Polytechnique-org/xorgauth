#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is distributed under the GPLv3 license.
# Copyright (c) Polytechnique.org


import codecs
import os
import re
import sys

from setuptools import find_packages, setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


def clean_readme(fname):
    """Cleanup README.rst for proper PyPI formatting."""
    with codecs.open(fname, 'r', 'utf-8') as f:
        return ''.join(
            re.sub(r':\w+:`([^`]+?)( <[^<>]+>)?`', r'``\1``', line)
            for line in f
            if not (line.startswith('.. currentmodule') or line.startswith('.. toctree'))
        )


PACKAGE = 'xorgauth'


setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    author="Polytechnique.org dev team",
    author_email="devel+xorgauth@staff.polytechnique.org",
    description="Polytechnique.org authentication provider",
    long_description=clean_readme('README.rst'),
    license='AGPLv3',
    keywords=['sso', 'authentication', 'authgroupex', 'openid connect'],
    url='https://github.com/Polytechnique-org/%s' % PACKAGE,
    download_url='http://pypi.python.org/pypi/%s/' % PACKAGE,

    packages=find_packages(include=[PACKAGE, '%s.*' % PACKAGE]),
    include_package_data=True,

    python_requires='>=3.4.2' if sys.version_info >= (3,) else '>=2.7',
    install_requires=[
        'Django>=5.0',
        'django-oidc-provider>=0.7.0',  # Version 0.7.0 has a breaking change in response types
        'django-bootstrap5',
        'django_zxcvbn_password',
        'getconf',
    ],
    setup_requires=[
        'setuptools>=0.8',
    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: French',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Languge :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP :: Session',
        'Topic :: System :: Systems Administration :: Authentication/Directory'
    ],
    test_suite='tests',
)
