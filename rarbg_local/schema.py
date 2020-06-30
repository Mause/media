from types import MethodType
from typing import Type, cast

from dataclasses_json import DataClassJsonMixin
from flask_restx import fields


def schema(clazz: Type, **kwargs):
    clx = type(cast(MethodType, DataClassJsonMixin.schema).__func__(clazz))
    return type(clazz.__name__ + 'Schema', (clx,), {})(**kwargs)


class TTuple(fields.Raw):
    def __init__(self, items):
        self.items = [item() if isinstance(item, type) else item for item in items]
        self.__schema_example__ = [
            item.example or item.__schema_example__ for item in self.items
        ]
        self.__schema_type__ = 'array'
        super().__init__()

    @property
    def __schema__(self):
        schema = super().__schema__
        schema.update({"items": [item.__schema__ for item in self.items]})
        return schema

    def output(self, key, data):
        data = fields.get_value(key, data)

        return [field.output(idx, data) for idx, field in enumerate(self.items)]


class DDict(fields.Wildcard):
    __schema_type__ = 'object'

    def __init__(self, container):
        super().__init__(container)
        self.__schema_example__ = {
            'additionalField1': self.container.example
            or self.container.__schema_example__
        }

    def output(self, key, data, ordered=False):
        data = fields.get_value(key, data)

        return {key: self.container.output(key, data) for key in data}
