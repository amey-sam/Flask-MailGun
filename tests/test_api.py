# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:33:58 2016

@author: richard
"""
import unittest
from tests import MailgunTestBase


class MailGunApiTest(MailgunTestBase):
    def test_sendpoint(self):
        self.assertEqual(self.mailgun.mailgun_api.sendpoint,
                         'https://api.mailgun.net/v3/example.com/messages')

    def test_routpoint(self):
        self.assertEqual(self.mailgun.mailgun_api.routepoint,
                         'https://api.mailgun.net/v3/routes')

if __name__ == '__main__':
    unittest.main()
