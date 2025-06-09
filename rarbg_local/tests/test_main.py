import pytest

from ..db import normalise_db_url
from ..main import normalise
from ..models import Episode

episodes: list[Episode] = [
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


@pytest.mark.parametrize(
    'original,expected',
    [
        (
            'postgres://user:pass@localhost:5432/db',
            'postgresql+asyncpg://user:pass@localhost:5432/db',
        ),
        ('sqlite:///:memory:', 'sqlite+aiosqlite:///:memory:'),
    ],
)
def test_normalise_db_url(original, expected) -> None:
    assert normalise_db_url(original).render_as_string(hide_password=False) == expected
