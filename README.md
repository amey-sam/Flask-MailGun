# Flask-MailGun


[![Latest Version](https://img.shields.io/pypi/v/flask-mailgun3.svg)](https://pypi.python.org/pypi/Flask-MailGun3)
[![Build Status](https://travis-ci.org/amey-sam/Flask-MailGun.svg?branch=master)](https://travis-ci.org/amey-sam/Flask-MailGun/builds/)
[![Coverage Status](https://coveralls.io/repos/github/amey-sam/Flask-MailGun/badge.svg?branch=master)](https://coveralls.io/github/amey-sam/Flask-MailGun?branch=master)
[![Code Climate](https://codeclimate.com/github/amey-sam/Flask-MailGun/badges/gpa.svg)](https://codeclimate.com/github/amey-sam/Flask-MailGun)
[![Python Versions](https://img.shields.io/pypi/pyversions/flask-mailgun3.svg)](https://pypi.python.org/pypi/Flask-MailGun3)
[![License](https://img.shields.io/pypi/l/Flask-MailGun3.svg)](https://pypi.python.org/pypi/Flask-MailGun3)
[![Downloads](https://img.shields.io/pypi/dm/flask-mailgun3.svg)](https://pypi.python.org/pypi/Flask-Mailgun3)

Flask-MailGun Flask extension to use the [MailGun](https://mailgun.com) email parsing service for sending and receiving emails.

## What it does

Flask-MailGun allows you to configure your connection into the MailGun api so that you can
- Send emails
- Set up routes
- Handle incoming emails
- `flask-mailgun3 >= 0.1.4` should work with `flask_security` as a drop in replacement for `flask_mail`

## Usage

```python
from flask_mailgun import MailGun

mailgun = MailGun()

# .. later
mailgun.init_app(app)

# ..some other time
@mailgun.on_attachment
def save_attachment(email, attachment):
    data = attachment.read()
    with open(attachment.filename, "w") as f:
        f.write(data)

# .. even later register the upload endpoint
mailgun.route('/uploads')

# send an email like flask_mail
message = Message()
message.subject = "Hello World"
message.sender = "from@example.com"
message.add_recipient("u1@example.com")
message.add_recipient("u2@example.com")
message.body = "Testing some Mailgun awesomness!"

mailgun.send(message)
```

## Long Requests

A mechanisom has been put in place to simplify handling long requests. Basically if your callback function blocks the processing of an email for toolong it will cause the post from the mailgun services to timeout. At the moment this is done by setting the `mailgun.callback_handeler` to `mailgun.async` but you would have to do this before registering the callbacks (you could reregister on init as well).
```python
# at config
app.config['MAILGUN_BG_PROCESSES'] = flask_mailgun.processing.async_pool(NO_PROCS)
app.config['MAILGUN_CALLBACK_HANDELER'] = app.config['MAILGUN_BG_PROCESSES']
# or later
mailgun.callback_handeler = mailgun.async

# but you may still have to :(
mailgun._on_attachment = [mailgun.async(func) for func in mailgun._on_attachment]
```

Async will save the attachment to disk and offload your callback to a process pool, handling all the file opperations and file cleanup for you.

This however is probably not an ideal system (threadding dosnt go to well with flask and the process pool implimentation is not simple), and for something more robust we need to move to a celary based system. Setting up celary server and taksks however are beyond the scope of this extension, (we will provide an example though). In addition it may be beniffichial to move to a notify fetch pattern instead of mailgun posting the email to us, however the implimentation details will remain internal to `flask_mailgun` and the api for `process_attachment` shouldn't change.
