from functools import lru_cache as _lru_cache
from typing import Set

_caches: Set[_lru_cache] = set()  # type: ignore


def lru_cache(*args, **kwargs):
    def wrapper(func):
        cache = _lru_cache(*args, **kwargs)(func)
        _caches.add(cache)
        return cache

    return wrapper


def cache_clear():
    while _caches:
        cache = _caches.pop()
        cache.cache_clear()  # type: ignore
