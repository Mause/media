import pytest
from main import normalise


seasons = [[{'Title': '1:23:45'}]]


@pytest.mark.parametrize(
    'original,expected',
    [
        [
            'Chernobyl.S01E01.1.23.45.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]',
            'Chernobyl.S00E00.TITLE.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]',
        ]
    ],
)
def test_normalise(original, expected):
    assert normalise(seasons, original) == expected
