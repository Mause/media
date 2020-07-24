from typing import Dict, List
from unittest.mock import MagicMock

import pytest

from ..main import normalise
from ..providers import threadable

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


def test_threadable():
    m = MagicMock(__name__='Test Thing', return_value=[3])

    results: List[int] = list(threadable([m], (1, 2)))

    assert results == [3]
    m.assert_called_with(1, 2)
