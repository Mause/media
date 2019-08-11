from typing import Set
from functools import lru_cache as _lru_cache


_caches: Set[_lru_cache] = set()


def lru_cache(*args, **kwargs):
    def wrapper(func):
        cache = _lru_cache(*args, **kwargs)(func)
        _caches.add(cache)
        return cache
    return wrapper


def cache_clear():
    while _caches:
        cache = _caches.pop()
        cache.cache_clear()
