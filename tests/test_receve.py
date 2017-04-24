# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 14:05:26 2017

@author: richard
"""
from __future__ import print_function
import unittest
import time
from flask_mailgun.utils import MailGunException
from mock import MagicMock

from tests import MailgunTestBase
from tests.fixtures.email import make_email_request, make_email, sign_email


class ReceiveMessageTest(MailgunTestBase):

    def test_email_verify(self):
        email = make_email()
        # assert error if email not signed
        with self.assertRaises(MailGunException):
            self.mailgun.mailgun_api.verify_email(email)
        # test runs without error on signed email
        email = sign_email(email, self.mailgun)
        self.mailgun.mailgun_api.verify_email(email)

    def test_receive_message(self):
        request = make_email_request(self.mailgun)
        # files = request.pop('files',[])
        self.mailgun.route('user', '/upload')
        response = self.appclient.post('/upload', data=request)
        self.assertEqual(response.status_code, 200)
        # self.mailgun.process_email(request)


class ReceiveMessageCallbacksTest(MailgunTestBase):

    def setUp(self):
        super(ReceiveMessageCallbacksTest, self).setUp()
        self.mailgun.route('user', '/upload')

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
            for i in range(10):
                time.sleep(0.1)

            return responce


class ReceiveMessageSyncTest(ReceiveMessageCallbacksTest):

    def test_receive_message(self):
        response = self.appclient.post('/upload', data=self.email)
        self.assertEqual(response.status_code, 200)
        time.sleep(1)
        self.assertEqual(self.receve_email_mock.call_count, 1)
        self.assertEqual(self.attachment_mock.call_count, 1)
        print ("received email")


class ReceiveMessageAsyncTest(ReceiveMessageCallbacksTest):

    def setUp(self):
        super(ReceiveMessageAsyncTest, self).setUp()
        self.email1 = make_email_request(self.mailgun)
        self.email2 = make_email_request(self.mailgun)
        # re register callbacks as async
        self.mailgun.callback_handeler = self.mailgun.processor.async
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
        print ("received 2 emails")

    def test_receive_100_messages(self):
        for i in range(100):
            email = make_email_request(self.mailgun)
            response = self.appclient.post('/upload', data=email)
            self.assertEqual(response.status_code, 200)
        # self.assertEqual(self.receve_email_mock.call_count, 100)
        # self.assertEqual(self.attachment_mock.call_count, 100)
        print ("received 100 emails")


if __name__ == '__main__':
    unittest.main()
