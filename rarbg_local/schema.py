from typing import Type

from dataclasses_json import DataClassJsonMixin
from flask_restx import fields


def schema(clazz: Type, **kwargs):
    clx = type(DataClassJsonMixin.schema.__func__(clazz))
    return type(clazz.__name__ + 'Schema', (clx,), {})(**kwargs)


class TTuple(fields.Raw):
    def __init__(self, items):
        super().__init__()
        self.items = [item() if isinstance(item, type) else item for item in items]

    @property
    def __schema__(self):
        return [item.__schema__ for item in self.items]

    def output(self, idx, data):
        return [
            field.output(idx, subdata)
            for idx, (field, subdata) in enumerate(zip(self.items, data))
        ]
