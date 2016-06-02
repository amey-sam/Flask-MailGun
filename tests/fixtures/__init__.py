# -*- coding: utf-8 -*-
"""
Created on Wed May 11 13:30:09 2016

@author: richard
"""
import os


def get_attachment():
    filename = "test_attachment.txt"
    fixture_dir = os.path.dirname(__file__)
    f_name = os.path.join(fixture_dir, filename)
    file_stream = open(f_name, "r")
    return (filename, file_stream)
