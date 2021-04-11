#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask-MailGun
Flask extension to use the Mailgun email parsing service
for sending and receving emails
"""
try: # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements

from io import open
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('Version', encoding='utf-8') as f:
    version = next(f).strip()

with open('README.rst', encoding='utf-8') as f:
    readme = f.read()

# parse_requirements() returns generator of pip.req.InstallRequirement objects
requirements = list(parse_requirements('requirements.txt', session=False))
try:
    requirements = [str(ir.req) for ir in requirements]
except AttributeError:
    # pip > 20
    requirements = [str(ir.requirement) for ir in requirements]

__NAME__ = 'Flask-MailGun3'
__doc__ = readme
__author__ = 'Amey-SAM'
__license__ = 'MIT'
__copyright__ = '2016'

setup(
    name=__NAME__,
    version=version,
    license=__license__,
    description='Flask extension to use the Mailgun email parsing service',
    long_description=__doc__,
    author=__author__,
    author_email='richard.mathie@amey.co.uk',
    url='https://github.com/amey-sam/Flask-MailGun',
    download_url='https://github.com/amey-sam/Flask-MailGun/tarball/master',
    # py_modules=['flask_mailgun'],
    packages=['flask_mailgun'],
    install_requires=requirements,
    keywords=['flask', 'mailgun'],
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

