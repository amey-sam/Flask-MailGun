# Flask-MailGun
Flask MailGun extension to use the [MailGun](https://mailgun.com) email parsing service for sending and receiving emails.

## What it dose works

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
def save_attachment(email, filename, fstream)
    data = fstream.read()
    with open(filename, "w") as f:
        f.write(data)

# .. even later
mailgun.create_route('/uploads')
```
