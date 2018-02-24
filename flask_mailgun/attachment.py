# -*- coding: utf-8 -*-
"""
Created on Thur Apr 20 13:56:10 2017

@author: richard.mathie@amey.co.uk
"""
from decorator import decorator
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from threading import Thread

import shutil
import tempfile
import os


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
def attachment_decorator(f, email, filename):
    """Converts a file back into a FileStorage Object"""
    with open(filename, 'r') as file:
        attachment = FileStorage(stream=file,
                                 filename=filename)
        result = f(email, attachment)
    return result


def save_attachments(attachments, tempdir=None):
    if not tempdir:
        tempdir = tempfile.mkdtemp()
    filenames = [secure_filename(att.filename) for att in attachments]
    filenames = [os.path.join(tempdir, name) for name in filenames]
    for (filename, attachment) in zip(filenames, attachments):
        attachment.save(filename)
    return filenames


def process_attachments(email, attachments, functions):
    tempdir = tempfile.mkdtemp()
    filenames = save_attachments(attachments, tempdir)
    results = [func(email, fname)
               for func in functions
               for fname in filenames]

    cleanup = Thread(target=clean_up, args=(results, tempdir))
    cleanup.start()


def clean_up(results, tempdir):
    """Clean up after an email is procesed

    Take the returned Async Results and wait for all results to return
    before removing temporary folder
    """
    for result in results:
        try:
            result.wait()
        except AttributeError:
            """Not Async"""
    shutil.rmtree(tempdir)
    return 1


class Attachment(object):
    """Encapsulates file attachment information.
    :versionadded: 0.3.5
    :param filename: filename of attachment
    :param content_type: file mimetype
    :param data: the raw file data
    :param disposition: content-disposition (if any)
    """

    def __init__(self, filename=None, content_type=None, data=None,
                 disposition=None, headers=None):
        self.filename = filename
        self.content_type = content_type
        self.data = data
        self.disposition = disposition or 'attachment'
        self.headers = headers or {}
