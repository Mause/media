from functools import lru_cache as _lru_cache
from typing import Protocol, TypeVar

from asyncache import cached as _cached
from cachetools.func import ttl_cache as _ttl_cache


class LRUCache(Protocol):
    def cache_clear(self):
        pass


T = TypeVar('T')
_caches: set[LRUCache] = set()


def lru_cache(*args, **kwargs):
    def wrapper(func):
        cache = _lru_cache(*args, **kwargs)(func)
        _caches.add(cache)
        return cache

    return wrapper


def ttl_cache(*args, **kwargs):
    def wrapper(func):
        cache = _ttl_cache(*args, **kwargs)(func)
        _caches.add(cache)
        return cache

    return wrapper


def cached(cache):
    def wrapper(func):
        c = _cached(cache)(func)
        _caches.add(type('', (), {'cache_clear': cache.clear}))
        return c

    return wrapper


def cache_clear():
    for c in _caches:
        c.cache_clear()


class NullPointerException(Exception):
    pass


def non_null(thing: T | None) -> T:
    if not thing:
        raise NullPointerException()
    return thing


def precondition(res: T | None, message: str) -> T:
    if not res:
        raise AssertionError(message)
    return res
