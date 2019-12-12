from functools import lru_cache

from .client import get_client

transmission = lru_cache()(get_client)


def __getattr__(name):
    return transmission().__getattr__(name)
