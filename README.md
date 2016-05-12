# Flask-MailGun


[![Latest Version](https://img.shields.io/pypi/v/flask-mailgun3.svg)](https://pypi.python.org/pypi/Flask-MailGun3)
[![Build Status](https://travis-ci.org/amey-sam/Flask-MailGun.svg?branch=master)](https://travis-ci.org/amey-sam/Flask-MailGun/builds/)
[![Coverage Status](https://coveralls.io/repos/github/amey-sam/Flask-MailGun/badge.svg?branch=master)](https://coveralls.io/github/amey-sam/Flask-MailGun?branch=master)
[![Code Climate](https://codeclimate.com/github/amey-sam/Flask-MailGun/badges/gpa.svg)](https://codeclimate.com/github/amey-sam/Flask-MailGun)
[![Python Versions](https://img.shields.io/pypi/pyversions/flask-mailgun3.svg)](https://pypi.python.org/pypi/Flask-MailGun3)
[![License](https://img.shields.io/pypi/l/Flask-MailGun3.svg)](https://pypi.python.org/pypi/Flask-MailGun3)
[![Downloads](https://img.shields.io/pypi/dm/flask-mailgun3.svg)](https://pypi.python.org/pypi/Flask-Mailgun3)

Flask MailGun extension to use the [MailGun](https://mailgun.com) email parsing service for sending and receiving emails.

## What it does

Flask-MailGun allows you to configure your connection into the MailGun api so that you can
- Send emails
- Set up routes
- Handel incoming emails

## Usage

```python
from flask_mailgun import MailGun

mailgun = MailGun()

# .. later
mailgun.init_app(app)

# ..some other time
@mailgun.on_attachment
def save_attachment(email, filename, fstream):
    data = fstream.read()
    with open(filename, "w") as f:
        f.write(data)

# .. even later
mailgun.create_route('/uploads')
```
