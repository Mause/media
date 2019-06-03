import pytest
from main import normalise


episodes = [{'name': '1:23:45'}, {}, {}, {'name': 'The Happiness of All Mankind'}]



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
    ],
)
def test_normalise(original, expected):
    assert normalise(episodes, original) == expected
