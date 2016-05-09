# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:41:03 2016

@author: richard
"""
import os

# MailGun parameters
MAILGUN_ROUTE = 'uploads'
MAILGUN_DOMAIN = 'example.com'
MAILGUN_API_URL = 'https://api.mailgun.net/v3'
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_HOST = 'example.com'
