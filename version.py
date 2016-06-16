# -*- coding: utf-8 -*-
"""
This module holds the version information so it only has to be changed
in one place. Based on `<http://bit.ly/16LbuJF>`_

:organization: Amey

Created on Mon Mar 21 16:45:27 2016

@author: richard
"""


def _safe_int(string):
    """ Simple function to convert strings into ints without dying. """
    try:
        return int(string)
    except ValueError:
        return string


__version__ = '0.1.2'
VERSION = tuple(_safe_int(x) for x in __version__.split('.'))
