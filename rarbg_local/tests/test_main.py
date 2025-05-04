from typing import List
from unittest.mock import MagicMock

import pytest

from ..db import normalise_db_url
from ..main import normalise
from ..models import Episode
from ..providers import threadable

episodes: List[Episode] = [
    Episode(name='1:23:45', episode_number=1, id=1),
    Episode(name='Open Wide, O Earth', episode_number=3, id=3),
    Episode(name='The Happiness of All Mankind', episode_number=4, id=4),
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
def test_normalise(original: str, expected: str) -> None:
    assert normalise(episodes, original) == expected


def test_threadable() -> None:
    m = MagicMock(__name__='Test Thing', return_value=[3])

    results: List[int] = list(threadable([m], (1, 2)))

    assert results == [3]
    m.assert_called_with(1, 2)


@pytest.mark.parametrize(
    'original,expected',
    [
        (
            'postgres://user:pass@localhost:5432/db',
            'postgresql://user:pass@localhost:5432/db',
        ),
        ('sqlite:///:memory:', 'sqlite:///:memory:'),
    ],
)
def test_normalise_db_url(original, expected) -> None:
    assert normalise_db_url(original).render_as_string(hide_password=False) == expected
