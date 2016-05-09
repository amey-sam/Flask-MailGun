# -*- coding: utf-8 -*-
"""
Created on Wed Jan 27 21:48:14 2016

@author: richard, yunxi
"""
import requests
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


@decorator
def async(f, *args, **kwargs):
    thread = Thread(target=f, args=args, kwargs=kwargs)
    thread.start()


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

        self.temp_file_dir = app.config['TEMP_FILE_DIR']
        self.allowed_extensions = app.config["ALLOWED_EXTENSIONS"]

    def send_email(self, **kwargs):
        if not self.mailgun_api:
            raise ValueError('A valid app instance has not been provided')

        default_from = self.app.config.get('MAILGUN_DEFAULT_FROM')
        if default_from:
            kwargs.setdefault('from', default_from)

        return self.mailgun_api.send_email(**kwargs)

    def create_route(self, dest='/messages/'):
        self.app.route(dest, methods=['POST'])(self.process_email)
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
        def process_attachment(email, filename, fstream)`
        """
        self._on_attachment.append(func)
        return func

    def process_email(self, request):
        """Function to pass to endpoint for processing incoming email post

        app.route('/incoming', methods=['POST'])(process_email)
        """
        email = request.form

        self.mailgun_api.__verify_email(email)
        # Process the attachments
        for func in self._on_attachment:
            if self.run_async:
                func = async(func)
            for attachment in request.files.values():
                func(email, attachment.filename, attachment.stream)
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
            text = 'Hello {} \n Yum Yum! you feed me at {}.' % (sender,
                                                                timestamp)

        self.send_email(**{'from': "%(route)s@%(domain)s" % self.__dict__,
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
        responce = requests.post(self.sendpoint, data=kwargs, auth=self.auth)
        responce.raise_for_status()
        return responce

    def create_route(self, dest='/messages/', data=None):
        self.dest = dest
        data = {"priority": 0,
                "description": "Sample route",
                "expression":
                "match_recipient('%(route)s@%(domain)s')" % self,
                "action": ["forward('http://%(host)s%(dest)s')" % self,
                           "stop()"]}
        return requests.post(self.api_url + 'routes',
                             auth=self.auth,
                             data=data)

    def __verify_email(self, email):
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


'''
-------------- REFERENCE ------------------

1. ========================== Fieds of request.form: ==========================

['stripped-signature',
 'Spamdiagnosticmetadata',
 'From',
 'X-Envelope-From',
 'X-Ms-Tnef-Correlator',
 'To',
 'Thread-Topic',
 'X-Microsoft-Exchange-Diagnostics',
 'Dkim-Signature',
 'X-Ms-Exchange-Crosstenant-Fromentityheader',
 'Accept-Language',
 'X-Ms-Exchange-Crosstenant-Originalarrivaltime',
 'attachment-count',
 'X-Originatororg',
 'Thread-Index',
 'from',
 'Content-Language',
 'stripped-html',
 'Date',
 'Message-Id',
 'body-plain',
 'Mime-Version',
 'Received',
 'X-Ms-Exchange-Transport-Crosstenantheadersstamped',
 'content-id-map',
 'X-Ms-Exchange-Crosstenant-Id',
 'timestamp',
 'X-Forefront-Prvs',
 'subject',
 'body-html',
 'stripped-text',
 'recipient',
 'Spamdiagnosticoutput',
 'sender',
 'Subject',
 'X-Mailgun-Incoming',
 'X-Microsoft-Antispam',
 'token',
 'message-headers',
 'X-Exchange-Antispam-Report-Cfa-Test',
 'signature',
 'X-Forefront-Antispam-Report',
 'X-Ms-Has-Attach',
 'Content-Type',
 'X-Originating-Ip',
 'X-Ms-Office365-Filtering-Correlation-Id']

2. =========================== fields of request: =============================

['__class__',
 '__delattr__',
 '__dict__',
 '__doc__',
 '__enter__',
 '__exit__',
 '__format__',
 '__getattribute__',
 '__hash__',
 '__init__',
 '__module__',
 '__new__',
 '__reduce__',
 '__reduce_ex__',
 '__repr__',
 '__setattr__',
 '__sizeof__',
 '__str__',
 '__subclasshook__',
 '__weakref__',
 '_get_file_stream',
 '_get_stream_for_parsing',
 '_is_old_module',
 '_load_form_data',
 '_parse_content_type',
 '_parsed_content_type',
 'accept_charsets',
 'accept_encodings',
 'accept_languages',
 'accept_mimetypes',
 'access_route',
 'application',
 'args',
 'authorization',
 'base_url',
 'blueprint',
 'cache_control',
 'charset',
 'close',
 'content_encoding',
 'content_length',
 'content_md5',
 'content_type',
 'cookies',
 'data',
 'date',
 'dict_storage_class',
 'disable_data_descriptor',
 'encoding_errors',
 'endpoint',
 'environ',
 'files',
 'form',
 'form_data_parser_class',
 'from_values',
 'full_path',
 'get_data',
 'get_json',
 'headers',
 'host',
 'host_url',
 'if_match',
 'if_modified_since',
 'if_none_match',
 'if_range',
 'if_unmodified_since',
 'input_stream',
 'is_multiprocess',
 'is_multithread',
 'is_run_once',
 'is_secure',
 'is_xhr',
 'json',
 'list_storage_class',
 'make_form_data_parser',
 'max_content_length',
 'max_form_memory_size',
 'max_forwards',
 'method',
 'mimetype',
 'mimetype_params',
 'module',
 'on_json_loading_failed',
 'parameter_storage_class',
 'path',
 'pragma',
 'query_string',
 'range',
 'referrer',
 'remote_addr',
 'remote_user',
 'routing_exception',
 'scheme',
 'script_root',
 'shallow',
 'stream',
 'trusted_hosts',
 'url',
 'url_charset',
 'url_root',
 'url_rule',
 'user_agent',
 'values',
 'view_args',
 'want_form_data_parsed']


'''
