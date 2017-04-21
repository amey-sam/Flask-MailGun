# -*- coding: utf-8 -*-
"""
Created on Thur Apr 20 13:56:10 2017

@author: richard.mathie@amey.co.uk
"""
from flask import request

from .api import MailGunAPI
from .processing import Processor
from .attachment import (attachment_decorator,
                         ALL_EXTENSIONS,
                         process_attachments)


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
        self.processor = Processor(app)
        self.callback_handeler = self.processor.process

        domain = app.config.get('MAILGUN_DOMAIN', 'localhost')
        self.default_sender = app.config.get('MAILGUN_DEFAULT_FROM',
                                             'no-reply@' + domain)
        # call back lists
        self._on_receive = []
        self._on_attachment = []

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['mail'] = self

        # self.temp_file_dir = app.config['TEMP_FILE_DIR']
        # self.allowed_extensions = app.config["ALLOWED_EXTENSIONS"]

    def send(self, message):
        return self.mailgun_api.send(message)

    def send_message(self, *args, **kwargs):
        return self.mailgun_api.send_message(*args, **kwargs)

    def route(self, recipient='user', dest='/messages/', priority=0):
        """Create the mailgun route and register endpoint with flask app

        this needs to be done after `mailgun.app_init`
        """
        # register the process_email endpoint with the flask app
        @self.app.route(dest, methods=['POST'])
        def mail_endpoint():
            return self.process_email(request)

        # register the endpoint route with mailgun
        return self.mailgun_api.create_route(recipient, dest, priority)

    def on_receive(self, func):
        """Register callback function with mailgun

        `@mailgun.on_receive
        def process_email(email)`
        """
        self._on_receive.append(self.callback_handeler(func))
        return func

    def on_attachment(self, func):
        """Register callback function with mailgun

        `@mailgun.on_attachment
        def process_attachment(email, filestorage)`
        """
        new_func = self.callback_handeler(attachment_decorator(func))
        self._on_attachment.append(new_func)
        return func

    def get_attachments(self, request):
        files = request.files.values()
        attachments = [att for att in files if self._is_file_allowed(att.filename)]
        return attachments

    def process_email(self, request):
        """Function to pass to endpoint for processing incoming email post

        app.route('/incoming', methods=['POST'])(process_email)
        """
        email = request.form
        self.mailgun_api.verify_email(email)
        # Process the attachments
        attachments = self.get_attachments(request)

        process_attachments(email, attachments, self._on_attachment)

        # Process the email
        for func in self._on_receive:
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
            message = 'Hello {} \n Thanks for the data! you feed me at {}.'
            text = message.format(sender, timestamp)
        # recipient = "%(route)s@%(domain)s" % self.mailgun_api.__dict__
        self.send_message(sender=recipient,
                          recipients=[sender],
                          subject=subject,
                          body=text)

    def _is_file_allowed(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

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
