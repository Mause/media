import json
from pathlib import Path
from typing import Callable

from aioresponses import aioresponses as Aioresponses
from pytest import fixture, mark
from pytest_snapshot.plugin import Snapshot

from ...providers.horriblesubs import (
    HorriblesubsDownloadType,
    HorriblesubsProvider,
    get_downloads,
    get_latest,
)
from ...types import ImdbId, TmdbId
from ..conftest import add_json, themoviedb, tolist
from ..factories import TvApiResponseFactory


@fixture
def load_html(resource_path: Path) -> Callable[[str], str]:
    def load_html(filename: str) -> str:
        return (resource_path / filename).read_text()
    return load_html


@mark.asyncio
async def test_parse(
    aioresponses: Aioresponses, load_html: Callable[[str], str]
) -> None:
    aioresponses.add(
        'https://horriblesubs.info/api.php?method=getlatest',
        'GET',
        body=load_html('test_parse.html'),
    )

    shows = await get_latest()

    assert shows == {
        'Boruto - Naruto Next Generations': '/shows/boruto-naruto-next-generations',
        'Gegege no Kitarou (2018)': '/shows/gegege-no-kitarou-2018',
        'One Piece': '/shows/one-piece',
        'Kyokou Suiri': '/shows/kyokou-suiri',
        'Magia Record': '/shows/magia-record',
        'Fate Grand Order - Absolute Demonic Front Babylonia': (
            '/shows/fate-grand-order-absolute-demonic-front-babylonia'
        ),
        'Nanabun no Nijyuuni': '/shows/nanabun-no-nijyuuni',
        'Ishuzoku Reviewers': '/shows/ishuzoku-reviewers',
        'Boku no Tonari ni Ankoku Hakaishin ga Imasu': (
            '/shows/boku-no-tonari-ni-ankoku-hakaishin-ga-imasu'
        ),
        'Cardfight!! Vanguard - Zoku Koukousei-hen': (
            '/shows/cardfight-vanguard-zoku-koukousei-hen'
        ),
        'Detective Conan': '/shows/detective-conan',
        'Boku no Hero Academia': '/shows/boku-no-hero-academia',
        'Runway de Waratte': '/shows/runway-de-waratte',
    }


def mock(aioresponses: Aioresponses, url: str, html: str) -> None:
    aioresponses.add(url + '&nextid=0', 'GET', body=html)
    aioresponses.add(
        url + '&nextid=1', 'GET', body='There are no batches for this show yet'
    )


def magnet_link(torrent_hash: str) -> str:
    return f'magnet:?xt=urn:btih:{torrent_hash}&tr=udp://tracker.coppersurfer.tk:6969/announce&tr=udp://tracker.internetwarriors.net:1337/announce&tr=udp://tracker.leechersparadise.org:6969/announce&tr=udp://tracker.opentrackr.org:1337/announce&tr=udp://open.stealth.si:80/announce&tr=udp://p4p.arenabg.com:1337/announce&tr=udp://mgtracker.org:6969/announce&tr=udp://tracker.tiny-vps.com:6969/announce&tr=udp://peerfect.org:6969/announce&tr=http://share.camoe.cn:8080/announce&tr=http://t.nyaatracker.com:80/announce&tr=https://open.kickasstracker.com:443/announce'


@mark.asyncio
async def test_get_downloads(
    aioresponses: Aioresponses, load_html: Callable[[str], str]
) -> None:
    mock(
        aioresponses,
        'https://horriblesubs.info/api.php?method=getshows&type=batch&showid=1',
        load_html('results.html'),
    )

    batches = await tolist(get_downloads(1, HorriblesubsDownloadType.BATCH))

    assert batches == [
        {
            "episode": "01-12",
            "resolution": "1080",
            "download": magnet_link("2UIBW66DGKSND7QKUBFE5WOGS2SCY2ZE"),
        },
        {
            'download': magnet_link('VO6CAWGQEKD2NVRMR3R2ZLU74LC5DFSC'),
            'episode': '01-12',
            'resolution': '720',
        },
        {
            'download': magnet_link('ACKN4HMMEZQVZQRWFQNGCOTSPKAPEJGI'),
            'episode': '01-12',
            'resolution': '480',
        },
    ]


@mark.asyncio
async def test_get_downloads_single(
    aioresponses: Aioresponses, snapshot: Snapshot, load_html: Callable[[str], str]
) -> None:
    mock(
        aioresponses,
        'https://horriblesubs.info/api.php?method=getshows&type=show&showid=1',
        load_html('../show.html'),
    )

    magnets = await tolist(get_downloads(1, HorriblesubsDownloadType.SHOW))

    snapshot.assert_match(json.dumps(magnets, indent=2, default=repr), 'magnets.json')


@mark.asyncio
async def test_provider(
    aioresponses: Aioresponses, snapshot: Snapshot, load_html: Callable[[str], str]
) -> None:
    mock(
        aioresponses,
        'https://horriblesubs.info/api.php?method=getshows&type=show&showid=264',
        load_html('../show.html'),
    )
    aioresponses.add(
        'https://horriblesubs.info/shows/', 'GET', body=load_html('shows.html')
    )
    aioresponses.add(
        'https://horriblesubs.info/shows/little-busters',
        'GET',
        body=load_html('show_page.html'),
    )
    add_json(
        aioresponses,
        'GET',
        'https://api.jikan.moe/v4/anime?limit=1&q=Little+Busters%2521',
        {
            'data': [
                {
                    'title': 'Little Busters!',
                    'mal_id': '12345',
                    'title_synonyms': ['Busters that are little'],
                },
            ]
        },
    )
    themoviedb(
        aioresponses,
        '/tv/1',
        TvApiResponseFactory.create(name='Little Busters!').model_dump(),
    )

    results = [
        item.model_dump()
        for item in await tolist(
            HorriblesubsProvider().search_for_tv(ImdbId('tt00000000'), TmdbId(1), 1, 2)
        )
    ]

    snapshot.assert_match(json.dumps(results, indent=2, default=repr), 'results.json')
