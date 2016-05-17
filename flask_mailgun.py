# -*- coding: utf-8 -*-
"""
Created on Wed Jan 27 21:48:14 2016

@author: richard, yunxi
"""
import requests
from flask import request
# For verification
import hashlib
import hmac
import os
from decorator import decorator
from threading import Thread


class MailGunException(Exception):
    pass

EXTENSIONS = {
    "TEXT": ["txt", "md"],
    "DOCUMENT": ["rtf", "odf", "ods", "gnumeric",
                 "abw", "doc", "docx", "xls", "xlsx", 'xlsb'],
    "IMAGE": ["jpg", "jpeg", "jpe", "png", "gif", "svg", "bmp", "webp"],
    "AUDIO": ["wav", "mp3", "aac", "ogg", "oga", "flac"],
    "DATA": ["csv", "ini", "json", "plist", "xml", "yaml", "yml"],
    "SCRIPT": ["js", "php", "pl", "py", "rb", "sh"],
    "ARCHIVE": ["gz", "bz2", "zip", "tar", "tgz", "txz", "7z"]
}

ALL_EXTENSIONS = EXTENSIONS["TEXT"] \
                 + EXTENSIONS["DOCUMENT"] \
                 + EXTENSIONS["IMAGE"] \
                 + EXTENSIONS["AUDIO"] \
                 + EXTENSIONS["DATA"] \
                 + EXTENSIONS["ARCHIVE"]

MAILGUN_API_URL = 'https://api.mailgun.net/v3'


@decorator
def async(f, *args, **kwargs):
    # this is not thread safe at the moment
    # TODO consider using celery or multiprocesing pool
    thread = Thread(target=f, args=args, kwargs=kwargs)
    thread.start()
    return thread


class MailGun(object):
    """MailGun Class"""
    app = None
    mailgun_api = None

    auto_reply = True
    run_async = True
    logger = None

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.mailgun_api = MailGunAPI(app.config)
        self._on_receive = []
        self._on_attachment = []

        # self.temp_file_dir = app.config['TEMP_FILE_DIR']
        # self.allowed_extensions = app.config["ALLOWED_EXTENSIONS"]

    def send_email(self, **kwargs):
        if not self.mailgun_api:
            raise ValueError('A valid app instance has not been provided')

        default_from = self.app.config.get('MAILGUN_DEFAULT_FROM')
        if default_from:
            kwargs.setdefault('from', default_from)

        return self.mailgun_api.send_email(**kwargs)

    def create_route(self, dest='/messages/'):
        """Create the mailgun route and register endpoint with flask app

        this needs to be done after `mailgun.app_init`"""

        # register the process_email endpoint with the flask app
        @self.app.route(dest, methods=['POST'])
        def mail_endpoint():
            return self.process_email(request)
        # register the endpoint route with mailgun
        return self.mailgun_api.create_route(dest)

    def on_receive(self, func):
        """Register callback function with mailgun

        `@mailgun.on_receive
        def process_email(email)`
        """
        self._on_receive.append(func)
        return func

    def on_attachment(self, func):
        """Register callback function with mailgun

        `@mailgun.on_attachment
        def process_attachment(email, filestorage)`
        """
        self._on_attachment.append(func)
        return func

    def process_email(self, request):
        """Function to pass to endpoint for processing incoming email post

        app.route('/incoming', methods=['POST'])(process_email)
        """
        email = request.form
        self.mailgun_api.verify_email(email)
        # Process the attachments
        for func in self._on_attachment:
            if self.run_async:
                func = async(func)
            for attachment in request.files.values():
                func(email, attachment)
                # data = attachment.stream.read()
                # with open(attachment.filename, "w") as f:
                #    f.write(data)
        # Process the email
        for func in self._on_receive:
            if self.run_async:
                func = async(func)
            func(email)
        # log and notify
        self.__log_status(request)
        if self.auto_reply:
            self.reply_sender(email)
        return "OK"

    def reply_sender(self, email, text=None):
        timestamp = email.get("timestamp")
        sender = email.get('from')
        recipient = email.get('To')
        subject = email.get('subject')
        if text is None:
            message = 'Hello {} \n Yum Yum! you feed me at {}.'
            text = message.format(sender,
                                  timestamp)
        recipient = "%(route)s@%(domain)s" % self.mailgun_api.__dict__
        self.send_email(**{'from': recipient,
                           'to': [sender],
                           'subject': subject,
                           'text': text})

    def _is_allowed_file(self, f_name):
        file_extension = os.path.splitext(f_name)[1].lower()
        return file_extension in self.allowed_extensions

    def __log_status(self, request):
        if self.logger:
            email = request.form
            return self.logger.log({
                "message": "Email received",
                "sender": email.get("sender"),
                "receiver": email.get("recipient"),
                "timestamp": email.get("timestamp"),
                "number_of_attachments": email.get("attachment-count"),
                "attachment_names": request.files.keys()}, "Info")


class MailGunAPI(object):
    def __init__(self, config):
        self.domain = config['MAILGUN_DOMAIN']
        self.api_key = config['MAILGUN_API_KEY']
        self.api_url = config.get('MAILGUN_API_URL',
                                  'https://api.mailgun.net/v2/')
        self.route = config.get('MAILGUN_ROUTE', 'uploads')
        self.host = config.get('MAILGUN_DOMAIN', self.domain)
        if self.api_key is None:
            raise MailGunException("No mailgun key supplied.")

    def send_email(self, **kwargs):
        files = kwargs.pop('files', [])
        responce = requests.post(self.sendpoint,
                                 data=kwargs,
                                 files=files,
                                 auth=self.auth)
        responce.raise_for_status()
        return responce

    def create_route(self, dest='/messages/', data=None,):
        self.dest = dest
        action = "forward('http://%(host)s%(dest)s')" % self.__dict__

        data = {"priority": 0,
                "description": "Sample route",
                "expression":
                "match_recipient('%(route)s@%(domain)s')" % self.__dict__,
                "action": [action, "stop()"]}

        return requests.post(self.api_url + 'routes',
                             auth=self.auth,
                             data=data)

    def verify_email(self, email):
        """Check that the email post came from mailgun

        see https://documentation.mailgun.com/user_manual.html#webhooks
        """
        if self.api_key is None:
            raise MailGunException("Mailbox Error: No MailGun API key is supplied.")

        signature = email.get("signature")
        token = email.get("token")
        timestamp = email.get("timestamp")

        if timestamp is None or token is None or signature is None:
            raise MailGunException("Mailbox Error: credential verification failed.", "Not enough parameters")

        signature_calc = hmac.new(key=self.api_key,
                                  msg='{}{}'.format(timestamp, token),
                                  digestmod=hashlib.sha256).hexdigest()
        if signature != signature_calc:
            raise MailGunException("Mailbox Error: credential verification failed.", "Signature doesn't match")

    @property
    def sendpoint(self):
        return '/'.join([self.api_url, self.domain, 'messages'])

    @property
    def auth(self):
        return ('api', self.api_key)
