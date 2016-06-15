# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:33:58 2016

@author: richard
"""
import os
import unittest
from mock import patch, MagicMock

from flask import Flask
import flask_mailgun
from tests import config
from tests.fixtures.email import make_email_request, make_email, sign_email
import time


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
        self.post_patcher = patch('flask_mailgun.requests.post')
        self.mailgun.mailgun_api.list_routes = MagicMock(return_value=[])
        self.mock_post = self.post_patcher.start()

    def tearDown(self):
        self.post_patcher.stop()


class MailGunApiTest(MailgunTestBase):
    def test_sendpoint(self):
        self.assertEqual(self.mailgun.mailgun_api.sendpoint,
                         'https://api.mailgun.net/v3/example.com/messages')

    def test_routpoint(self):
        self.assertEqual(self.mailgun.mailgun_api.routepoint,
                         'https://api.mailgun.net/v3/routes')


class SendMessageTest(MailgunTestBase):
    def test_send_simple_message(self):
        message = {"from": "from@example.com",
                   "to": ["user1@example.com", "user2@example.com"],
                   "subject": "Hello",
                   "text": "Testing some Mailgun awesomness!"}
        self.mailgun.send_email(**message)
        self.assertTrue(self.mock_post.called)
        url = self.mock_post.call_args[0][0]
        auth = self.mock_post.call_args[1]['auth']
        data = self.mock_post.call_args[1]['data']
        # files = self.mock_post.call_args[1]['files']
        self.assertEqual(url, 'https://api.mailgun.net/v3/example.com/messages')
        self.assertEqual(auth, ('api', 'testtesttest'))
        # self.assertEqual(files, [])
        self.assertEqual(data['from'], 'from@example.com')
        self.assertEqual(data['to'], message['to'])
        self.assertEqual(data['subject'], message['subject'])
        self.assertEqual(data['text'], message['text'])


class ReceiveMessageTest(MailgunTestBase):

    def test_email_verify(self):
        email = make_email()
        # assert error if email not signed
        with self.assertRaises(flask_mailgun.MailGunException):
            self.mailgun.mailgun_api.verify_email(email)
        # test runs without error on signed email
        email = sign_email(email, self.mailgun)
        self.mailgun.mailgun_api.verify_email(email)

    def test_receive_message(self):
        request = make_email_request(self.mailgun)
        # files = request.pop('files',[])
        self.mailgun.create_route('user', '/upload')
        response = self.appclient.post('/upload', data=request)
        self.assertEqual(response.status_code, 200)
        # self.mailgun.process_email(request)


class ReceiveMessageCallbacksTest(MailgunTestBase):

    def setUp(self):
        super(ReceiveMessageCallbacksTest, self).setUp()
        self.mailgun.create_route('user', '/upload')

        self.email = make_email_request(self.mailgun)

        self.receve_email_mock = MagicMock(name='receve_email')
        self.attachment_mock = MagicMock(name='attachment')

        @self.mailgun.on_receive
        def receive_email_func(*args, **kwargs):
            return self.receve_email_mock(*args, **kwargs)

        import time

        @self.mailgun.on_attachment
        def attachment_func(email, attachment):
            # print "processing on", os.getpid()
            responce = self.attachment_mock(email, attachment)
            data = attachment.read()
            len(data)
            for i in xrange(10):
                time.sleep(0.1)

            return responce


class ReceiveMessageSyncTest(ReceiveMessageCallbacksTest):

    def test_receive_message(self):
        response = self.appclient.post('/upload', data=self.email)
        self.assertEqual(response.status_code, 200)
        time.sleep(1)
        self.assertEqual(self.receve_email_mock.call_count, 1)
        self.assertEqual(self.attachment_mock.call_count, 1)
        print "received email"


class ReceiveMessageAsyncTest(ReceiveMessageCallbacksTest):

    def setUp(self):
        super(ReceiveMessageAsyncTest, self).setUp()
        self.email1 = make_email_request(self.mailgun)
        self.email2 = make_email_request(self.mailgun)
        # re register callbacks as async
        self.mailgun.callback_handeler = self.mailgun.async
        callbacks = self.mailgun._on_attachment
        self.mailgun._on_attachment = []
        for callback in callbacks:
            self.mailgun.on_attachment(callback)

    def test_receive_2_messages(self):
        response = self.appclient.post('/upload', data=self.email1)
        self.assertEqual(response.status_code, 200)
        response = self.appclient.post('/upload', data=self.email2)
        self.assertEqual(response.status_code, 200)
        time.sleep(1)
        # self.assertEqual(self.receve_email_mock.call_count, 2)
        # self.assertEqual(self.attachment_mock.call_count, 2)
        print "received 2 emails"

    def test_receive_100_messages(self):
        for i in xrange(100):
            email = make_email_request(self.mailgun)
            response = self.appclient.post('/upload', data=email)
            self.assertEqual(response.status_code, 200)
        # self.assertEqual(self.receve_email_mock.call_count, 100)
        # self.assertEqual(self.attachment_mock.call_count, 100)
        print "received 100 emails"

if __name__ == '__main__':
    unittest.main()
