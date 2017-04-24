# -*- coding: utf-8 -*-
"""
Created on Thur Apr 20 13:56:10 2017

@author: richard.mathie@amey.co.uk
"""
import requests
# For verification with the MailgunAPI
import hashlib
import hmac
import json
import os

from collections import defaultdict

from .utils import MailGunException
from .message import Message

MAILGUN_API_URL = 'https://api.mailgun.net/v3'


class MailGunAPI(object):
    def __init__(self, config):
        self.domain = config['MAILGUN_DOMAIN']
        self.api_key = config['MAILGUN_API_KEY'].encode('utf-8')
        self.api_url = config.get('MAILGUN_API_URL',
                                  MAILGUN_API_URL)
        self.route = config.get('MAILGUN_ROUTE', 'uploads')
        self.host = config.get('MAILGUN_HOST', self.domain)
        self.dest = '/messages/'
        if self.api_key is None:
            raise MailGunException("No mailgun key supplied.")

    def send(self, message, envelope_from=None):
        """Verifies and sends message.
        :param message: Message instance.
        :param envelope_from: Email address to be used in MAIL FROM command.
        """
        mesage_data = {'from': envelope_from or message.sender,
                       'to': message.send_to,
                       'subject': message.subject,
                       "cc": message.cc,
                       "bcc": message.bcc,
                       'text': message.body,
                       'html': message.html}
        mesage_data = {k: v for k, v in mesage_data.items() if v is not None}

        files = [(a.disposition, (a.filename, a.data))
                 for a in message.attachments]

        responce = requests.post(self.sendpoint,
                                 auth=self.auth,
                                 data=mesage_data,
                                 files=files)
        responce.raise_for_status()
        return responce

    def send_message(self, *args, **kwargs):
        """Shortcut for send(msg).
        Takes same arguments as Message constructor.
        :versionadded: 0.3.5
        """

        self.send(Message(*args, **kwargs))

    def list_routes(self):
        request = requests.get(self.routepoint,
                               auth=self.auth)
        if not request.ok:
            raise MailGunException("Failed to get routes. Please check your configuration e.g. your mailgun key.")
        return json.loads(request.text).get('items')

    def route_exists(self, route):
        routes = self.list_routes()

        expression_action = defaultdict(list)
        for r in routes:
            expression_action[r['expression']].extend(r['actions'])

        current_actions = expression_action[route['expression']]
        return set(route['action']) <= set(current_actions)

    def create_route(self, recipient='user', dest='/messages/', priority=0):

        route = self._build_route(recipient, dest, priority)
        # Create Route Only if it does not Exist # TODO should update?
        if self.route_exists(route):
            return None
        else:
            return requests.post(self.routepoint,
                                 auth=self.auth,
                                 data=route)

    def remove_route(self, dest):
        route_id = self.get_route_id(self._build_route(dest))
        if route_id:
            route_api = os.path.join(self.routepoint, route_id)
            ret = requests.delete(route_api, auth=self.auth)
            if ret.ok:
                return True
            else:
                raise MailGunException("Route deletion failed. Reason: " + ret.reason)
        return False

    def _build_route(self, recipient, dest=None, priority=0):
        """ Build a mailgun route dictionary
        """
        if not dest:
            dest = self.dest
        action = "forward('http://{}{}')".format(self.host, dest)
        expression = "match_recipient('{}@{}')".format(recipient, self.domain)
        return {"priority": priority,
                "description": "Route created by Flask-MailGun3",
                "expression": expression,
                "action": [action, "stop()"]}

    def get_route_id(self, route):
        """ Get id of the route
        Return: id of the route. None if not exist.
        """
        def make_key(_route):
            return _route["expression"].join(_route["action"])

        # TODO RPM YXI, not actually shure this is what we want...
        routes = self.list_routes()
        if routes:
            id_table = dict((make_key(r), r["id"]) for r in routes)
            return id_table.get(make_key(route)) 
        else:
            return None

    def verify_email(self, email):
        """Check that the email post came from mailgun

        see https://documentation.mailgun.com/user_manual.html#webhooks
        """
        signature = email.get("signature")
        token = email.get("token")
        timestamp = email.get("timestamp")

        if timestamp is None or token is None or signature is None:
            raise MailGunException("Mailbox Error: credential verification failed.", "Not enough parameters")

        message = '{}{}'.format(timestamp, token).encode('utf-8')
        signature_calc = hmac.new(key=self.api_key,
                                  msg=message,
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
        return 'api', self.api_key
