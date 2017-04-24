# import os
import time
# from flask_mailgun import async
from flask_mailgun.processing import async_pool
import unittest


def runner(fun):
    results = [fun(i) for i in range(20)]
    for result in results:
        result.wait()
        result.get()


def foo(arg):
    time.sleep(0.1)
    return arg


class AsyncTest(unittest.TestCase):

    def test_async(self):
        async_foo = async_pool(4)(foo)
        runner(async_foo)

if __name__ == '__main__':
    unittest.main()
