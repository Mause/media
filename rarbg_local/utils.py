from functools import lru_cache as _lru_cache
from functools import wraps
from typing import Callable, Optional, Set, TypeVar

from apispec.ext.marshmallow import MarshmallowPlugin, make_schema_key, resolver
from flask import request
from flask_restx import Api, Resource, fields
from flask_restx.model import SchemaModel
from marshmallow import Schema
from marshmallow import fields as mfields
from marshmallow_enum import EnumField

from .schema import DDict

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


def enum_field(field, ret):
    if isinstance(field, EnumField):
        return {'enum': [value.name for value in field.enum]}
    return {}


class Spec:
    api: Api

    def __init__(self):
        self.components = self
        self._schemas = self

    def schema(self, name, schema):
        self.api.schema_model(name, schema)
        mp.converter.refs[make_schema_key(schema)] = name

    def __contains__(self, name):
        return name in self.api.models


spec = Spec()

mp = MarshmallowPlugin()
mp.converter = mp.Converter("3.0.2", resolver, spec)
mp.converter.field_mapping[EnumField] = ('string', None)
mp.converter.attribute_functions.append(enum_field)


def schema_to_openapi(api: Api, name: str, schema: Schema) -> SchemaModel:
    spec.api = api
    s = api.schema_model(name, mp.schema_helper(name, None, schema=schema))
    if schema.many:
        s = [s]
    return s


def convert(api, name, field):
    if isinstance(field, mfields.List):
        return fields.List(convert(api, name, field.inner))
    elif isinstance(field, mfields.Nested):
        return fields.Nested(convert(api, name, field.nested))
    elif isinstance(field, Schema):
        return api.model(
            field.__class__.__name__,
            {name: convert(api, name, value) for name, value in field.fields.items()},
        )
    elif isinstance(field, type) and issubclass(field, mfields.SchemaABC):
        return convert(api, name, field())
    elif isinstance(field, mfields.Integer):
        return fields.Integer()
    elif isinstance(field, mfields.String):
        return fields.String()
    elif isinstance(field, mfields.Dict):
        return DDict(convert(api, name, field.value_field))
    elif isinstance(field, mfields.DateTime):
        return fields.String()
    else:
        raise Exception(field)


def schema_to_marshal(api: Api, name: str, schema: Schema):
    return convert(api, name, schema)


def unwrap(f):
    while hasattr(f, '__wrapped__'):
        f = f.__wrapped__
    return f


def ismethod(func):
    return '.' in getattr(func, '__qualname__', '')


def expect(api: Api, name: str, schema: Schema):
    def wrapper(func):
        @api.expect(schema_to_openapi(api, name, schema))
        @wraps(func)
        def decorator(*args, **kwargs):
            rq = schema.load(request.json)

            if ismethod(unwrap(func)):
                return func(args[0], rq, *args[1:], **kwargs)
            else:
                return func(rq, *args, **kwargs)

        return decorator

    return wrapper


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
