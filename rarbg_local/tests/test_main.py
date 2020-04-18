from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

import pytest
from dataclasses_json import DataClassJsonMixin
from flask import Flask
from flask_restx import Api, Swagger, fields

from ..main import normalise
from ..schema import TTuple, schema
from ..utils import as_resource, schema_to_openapi

episodes: List[Dict] = [
    {'name': '1:23:45', 'episode_number': 1},
    {'name': 'Open Wide, O Earth', 'episode_number': 3},
    {'name': 'The Happiness of All Mankind', 'episode_number': 4},
]


@pytest.mark.parametrize(
    'original,expected',
    [
        [
            'Chernobyl.S01E01.1.23.45.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]',
            'Chernobyl.S00E00.TITLE.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]',
        ],
        [
            'Chernobyl.S01E04.The.Happiness.of.All.Mankind.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]',
            'Chernobyl.S00E00.TITLE.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]',
        ],
        [
            'Chernobyl.S01E03.Open.Wide.O.Earth.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]',
            'Chernobyl.S00E00.TITLE.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]',
        ],
    ],
)
def test_normalise(original, expected):
    assert normalise(episodes, original) == expected


def test_schema_to_openapi():
    class Enumerable(Enum):
        A, B = 0, 1

    @dataclass
    class D(DataClassJsonMixin):
        field: Enumerable

    sc = schema(D)
    api = Api()
    result = schema_to_openapi(api, 'D', sc)
    assert result._schema == {
        'type': 'object',
        'properties': {'field': {'type': 'string', 'enum': ['A', 'B']}},
    }


def test_ttuple():
    api = Api()

    TestModel = api.model(
        'TestModel',
        {'field': TTuple([fields.String(example='hello'), fields.Integer(example=1)])},
    )

    swagger = Swagger(api)

    app = Flask('fake')
    app.config['SERVER_NAME'] = 'what'
    app.route('/', endpoint='root')(lambda: '')

    @api.route('/api')
    @api.expect(TestModel)
    @as_resource()
    def fake():
        ...

    with app.app_context():
        swagger_def = swagger.as_dict()

    TestModel = swagger_def['definitions']['TestModel']

    assert TestModel == {
        'type': 'object',
        'properties': {
            'field': {
                'example': ['hello', 1],
                'type': 'array',
                'items': [
                    {'type': 'string', 'example': 'hello'},
                    {'type': 'integer', 'example': 1},
                ],
            }
        },
    }
