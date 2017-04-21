# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:33:15 2016

@author: richard
"""
import unittest
from mock import patch, MagicMock

from flask import Flask
import flask_mailgun
import flask_mailgun.api
from tests import config


def get_app(name):
    app = Flask(name)
    app.config.from_object(config)
    return app


class MailgunTestBase(unittest.TestCase):
    def setUp(self):
        self.app = app = get_app('test')
        self.appclient = app.test_client()
        self.mailgun = flask_mailgun.MailGun()
        self.mailgun.init_app(app)
        self.post_patcher = patch('flask_mailgun.api.requests.post')
        self.mailgun.mailgun_api.list_routes = MagicMock(return_value=[])
        self.mock_post = self.post_patcher.start()

    def tearDown(self):
        self.post_patcher.stop()

    def test_allways(self):
        pass

if __name__ == '__main__':
    unittest.main()
