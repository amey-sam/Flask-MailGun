# import os
import time
# from flask_mailgun import async
from multiprocessing import Pool  # , active_children
from decorator import decorator  # , decorate
from functools import wraps
import unittest


# using decorator
@decorator
def async(f, *args, **kwargs):
    return pool.apply_async(f, args=args, kwds=kwargs)


# function decorator
def async_pool(pool_size):

    def wrapper(func):
        pool = Pool(pool_size)

        @wraps(func)
        def inner(*args, **kwargs):
            return pool.apply_async(func, args=args, kwds=kwargs)
        return inner
    return wrapper


# this one has fixed pool size
def run_async(func):
    pool = Pool(4)

    @wraps(func)
    def async_func(*args, **kwargs):
        return pool.apply_async(func, args=args, kwds=kwargs)

    return async_func


# as a class decorator
def Async(object):
    def __init__(self, func):
        self.func = func
        self.pool = Pool(4)

    def __call__(self, *args, **kwargs):
        return self.pool.apply_async(self.func, args=args, kwds=kwargs)


def foo(arg):
    time.sleep(1)
    print arg
    return arg

pool = Pool(5)


def runner(fun):
    results = [fun(i) for i in xrange(20)]
    for result in results:
        result.wait()
        print result.get()


class AsyncTest(unittest.TestCase):
    def test_async(self):
        async_foo = async(foo)
        runner(async_foo)


class Async2Test(unittest.TestCase):
    def test_async(self):
        async_foo = async_pool(4)(foo)
        runner(async_foo)

    def test_decorator(self):
        async = async_pool(4)

        def bar(arg):
            time.sleep(1)
            print arg
            return arg
        async_bar = async(bar)
        runner(async_bar)

    def test_decorator1(self):
        def baz(arg):
            time.sleep(1)
            print arg
            return arg
        boz = run_async(baz)
        runner(boz)


if __name__ == '__main__':
    unittest.main()
