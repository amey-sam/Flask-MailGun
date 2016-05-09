"""
Flask-MailGun
Flask extension to use the Mailgun email parsing service
for sending and receving emails
"""
import re
from pip.req import parse_requirements
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version():
    with open('version.py') as version_file:
        return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                         version_file.read()).group('version')


# parse_requirements() returns generator of pip.req.InstallRequirement objects
requirements = parse_requirements('requirements.txt', session=False)

# reqs is a list of requirement
install_requires = [str(ir.req) for ir in requirements]

__NAME__ = "Flask-MailGun"
__author__ = "Amey-SAM"
__license__ = "MIT"
__copyright__ = "2016"

config = {
    'name': __NAME__,
    'license': __license__,
    'description': 'Flask extension to use the Mailgun email parsing service',
    'long_description': __doc__,
    'author': __author__,
    'url': 'https://github.com/amey-sam/Flask-MailGun',
    'download_url': 'https://github.com/amey-sam/Flask-MailGun/tarball/master',
    'py_modules': ['flask_mailgun'],
    'author_email': 'richard.mathie@amey.co.uk',
    'version': get_version(),
    # 'packages': ['flask_mailgun'],
    'scripts': [],
    'install_requires': install_requires,
    'keywords': ["flask", "mailgun"],
    'zip_safe': False,
}

setup(**config)
