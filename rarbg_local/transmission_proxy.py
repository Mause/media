from functools import lru_cache

from .client import get_client

transmission = lru_cache()(get_client)


def __getattr__(name):
    return lambda *args, **kwargs: getattr(transmission(), name)(*args, **kwargs)
