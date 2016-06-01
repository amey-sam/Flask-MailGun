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
import json
import tempfile
from collections import defaultdict
from decorator import decorator
from threading import Thread
from multiprocessing import Pool
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


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
    return pool.apply_async(f, args=args, kwds=kwargs)


@decorator
def sync(f, *args, **kwargs):
    return f(*args, **kwargs)


@decorator
def attachment_decorator(f, email, filename):
    print "opening", filename, " on", os.getpid()
    with open(filename, 'r') as file:
        attachment = FileStorage(stream=file,
                                 filename=filename)
        result = f(email, attachment)
    return result

pool = Pool(5)


class MailGun(object):
    """MailGun Class"""
    app = None
    mailgun_api = None

    auto_reply = True
    logger = None

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.mailgun_api = MailGunAPI(app.config)
        self.allowed_extensions = app.config.get('ALLOWED_EXTENSIONS',
                                                 ALL_EXTENSIONS)
        self.callback_handeler = app.config.get('MAILGUN_CALLBACK_HANDELER',
                                                sync)
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

    def file_allowed(self, filename):
        return '.' in filename and \
           filename.rsplit('.', 1)[1] in self.allowed_extensions

    def get_attachments(self, request):
        files = request.files.values()
        attachments = [att for att in files if self.file_allowed(att.filename)]
        return attachments

    def save_attachments(self, attachments, tempdir=None):
        if not tempdir:
            tempdir = tempfile.mkdtemp()
        filenames = [os.path.join(tempdir,
                                  secure_filename(att.filename))
                     for att in attachments]
        for (filename, attachment) in zip(filenames, attachments):
            attachment.save(filename)
        return filenames

    def process_email(self, request):
        """Function to pass to endpoint for processing incoming email post

        app.route('/incoming', methods=['POST'])(process_email)
        """
        email = request.form
        self.mailgun_api.verify_email(email)

        # Process the attachments
        tempdir = './temp/'  # tempfile.mkdtemp()
        attachments = self.get_attachments(request)
        filenames = self.save_attachments(attachments, tempdir=tempdir)

        for func in self._on_attachment:
            func = self.callback_handeler(attachment_decorator(func))
            for attachment in filenames:
                func(email, attachment)

        # Process the email
        for func in self._on_receive:
            func = self.callback_handeler(func)
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

    def list_routes(self):
        request = requests.get(self.routepoint,
                               auth=self.auth)
        return json.loads(request.text).get('items')

    def route_exists(self, route):
        routes = self.list_routes()

        expression_action = defaultdict(list)
        for r in routes:
            expression_action[r['expression']].extend(r['actions'])

        current_actions = expression_action[route['expression']]
        return set(route['action']) <= set(current_actions)

    def create_route(self, dest='/messages/', data=None,):
        self.dest = dest
        action = "forward('http://%(host)s%(dest)s')" % self.__dict__

        route = {"priority": 0,
                 "description": "Sample route",
                 "expression":
                 "match_recipient('%(route)s@%(domain)s')" % self.__dict__,
                 "action": [action, "stop()"]}
        # Create Route Only if it does not Exist
        # TODO should not it update?
        if self.route_exists(route):
            return None
        else:
            return requests.post(self.routepoint,
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

    def api_route(self, *pieces):
        pieces = [self.api_url] + [p for p in pieces]
        return '/'.join(s.strip('/') for s in pieces)

    @property
    def sendpoint(self):
        return self.api_route(self.domain, 'messages')

    @property
    def routepoint(self):
        return self.api_route('routes')

    @property
    def auth(self):
        return ('api', self.api_key)
