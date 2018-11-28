from functools import wraps
from multiprocessing import Pool

from decorator import decorator


def async_pool(pool_size):
    def wrapper(func):
        pool = Pool(pool_size)

        @wraps(func)
        def inner(*args, **kwargs):
            return pool.apply_async(func, args=args, kwds=kwargs)
        return inner
    return wrapper


@decorator
def sync(f, *args, **kwargs):
    return f(*args, **kwargs)

class Processor:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.callback_handeler = app.config.get('MAILGUN_CALLBACK_HANDELER',
                                                sync)
        self.async_pool = async_pool(app.config.get('MAILGUN_BG_PROCESSES', 4))

        self.process = self.callback_handeler
