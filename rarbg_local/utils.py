from functools import lru_cache as _lru_cache
from typing import Dict, Optional, Set, TypeVar

from apispec.ext.marshmallow import MarshmallowPlugin
from marshmallow import Schema

T = TypeVar('T')
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


class NullPointerException(Exception):
    pass


def non_null(thing: Optional[T]) -> T:
    if not thing:
        raise NullPointerException()
    return thing


def precondition(res: Optional[T], message: str) -> None:
    if not res:
        raise AssertionError(message)


mp = MarshmallowPlugin()
mp.converter = mp.Converter("3.0.2", None, None)


def schema_to_openapi(name: str, schema: Schema) -> Dict:
    return mp.schema_helper(name, None, schema=schema)
