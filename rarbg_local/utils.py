from functools import lru_cache as _lru_cache
from functools import wraps
from typing import Callable, Optional, Set, TypeVar

from flask_restx import Resource

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


def precondition(res: Optional[T], message: str) -> T:
    if not res:
        raise AssertionError(message)
    return res


def as_resource(methods: Set[str] = None):
    '''
    Methods default to {'GET'}
    '''

    def wrapper(func: Callable):
        return type(
            func.__name__,
            (Resource,),
            {
                method.lower(): wraps(func)(
                    lambda self, *args, **kwargs: func(*args, **kwargs)
                )
                for method in (methods or {'GET'})
            },
        )

    return wrapper
