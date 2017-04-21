# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 12:06:50 2017

@author: richard
"""
import unittest

from tests import MailgunTestBase
from flask_mailgun.message import Message


class SendMessageTest(MailgunTestBase):
    def test_send_simple_message(self):
        message = Message(subject="Hello",
                          sender="from@example.com",
                          recipients=["u1@example.com", "u2@example.com"],
                          body="Testing some Mailgun awesomness!")
        self.mailgun.send(message)
        self.assertTrue(self.mock_post.called)
        url = self.mock_post.call_args[0][0]
        auth = self.mock_post.call_args[1]['auth']
        data = self.mock_post.call_args[1]['data']
        # files = self.mock_post.call_args[1]['files']
        self.assertEqual(url, 'https://api.mailgun.net/v3/example.com/messages')
        self.assertEqual(auth, ('api', 'testtesttest'))
        # self.assertEqual(files, [])
        self.assertEqual(data['from'], message.sender)
        self.assertEqual(data['to'], set(message.recipients))
        self.assertEqual(data['subject'], message.subject)
        self.assertEqual(data['text'], message.body)

if __name__ == '__main__':
    unittest.main()
