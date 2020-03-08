from functools import lru_cache as _lru_cache
from typing import Callable, List, Optional, Set, TypeVar

from apispec.ext.marshmallow import MarshmallowPlugin
from flask_restx import Api, Resource
from flask_restx.model import SchemaModel
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


def schema_to_openapi(api: Api, name: str, schema: Schema) -> SchemaModel:
    s = api.schema_model(name, mp.schema_helper(name, None, schema=schema))
    if schema.many:
        s = [s]
    return s


def as_resource(methods: List[str] = ['GET']):
    def wrapper(func: Callable):
        return type(
            func.__name__,
            (Resource,),
            {
                method.lower(): lambda self, *args, **kwargs: func(*args, **kwargs)
                for method in methods
            },
        )

    return wrapper
