# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 12:08:14 2016

@author: richard
"""
import unittest
import os
import shutil
import tempfile
from werkzeug import FileStorage
from tests.fixtures import get_attachment
from test_flask_mailgun import MailgunTestBase


class SaveAttachmentTest(MailgunTestBase):
    def setUp(self):
        super(SaveAttachmentTest, self).setUp()
        (filename, file_stream) = get_attachment()
        self.attachment = FileStorage(stream=file_stream,
                                      filename=filename)

    def tearDown(self):
        super(SaveAttachmentTest, self).tearDown()
        self.attachment.close()

    def test_fileallowed(self):
        self.assertTrue(self.mailgun.file_allowed('test.txt'))
        self.assertFalse(self.mailgun.file_allowed('bob'))

    def test_save_attachments(self):
        testdir = tempfile.mkdtemp()
        self.attachment.seek(0)
        filenames = self.mailgun.save_attachments([self.attachment], testdir)
        filenames = [os.path.basename(filename) for filename in filenames]
        self.assertTrue(set(os.listdir(testdir)) == set(filenames))
        self.assertEqual(len(os.listdir(testdir)), 1)
        shutil.rmtree(testdir)
        with self.assertRaises(OSError):
            os.listdir(testdir)

if __name__ == '__main__':
    unittest.main()
