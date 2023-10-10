#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask-MailGun
Flask extension to use the Mailgun email parsing service
for sending and receving emails
"""
from io import open
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('Version', encoding='utf-8') as f:
    version = next(f).strip()

with open('README.rst', encoding='utf-8') as f:
    readme = f.read()


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
    install_requires=[
      'Flask',
      'requests',
      'decorator',
    ],
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
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

