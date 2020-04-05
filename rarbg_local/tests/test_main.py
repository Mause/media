from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

import pytest
from dataclasses_json import DataClassJsonMixin
from flask_restx import Api

from ..main import normalise
from ..schema import schema
from ..utils import schema_to_openapi

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
