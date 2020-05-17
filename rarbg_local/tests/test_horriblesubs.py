from dataclasses import asdict
from pathlib import Path

from responses import RequestsMock

from ..horriblesubs import HorriblesubsDownloadType, get_downloads, get_latest
from ..providers import HorriblesubsProvider
from . import test_integration
from .conftest import themoviedb


def load_html(filename):
    with (Path(__file__).parent / 'resources' / filename).open('r') as fh:
        return fh.read()


def test_parse(responses):
    responses.add(
        'GET',
        'https://horriblesubs.info/api.php?method=getlatest',
        body=load_html('test_parse.html'),
    )

    shows = get_latest()

    assert shows == {
        'Boruto - Naruto Next Generations': '/shows/boruto-naruto-next-generations',
        'Gegege no Kitarou (2018)': '/shows/gegege-no-kitarou-2018',
        'One Piece': '/shows/one-piece',
        'Kyokou Suiri': '/shows/kyokou-suiri',
        'Magia Record': '/shows/magia-record',
        'Fate Grand Order - Absolute Demonic Front Babylonia': '/shows/fate-grand-order-absolute-demonic-front-babylonia',
        'Nanabun no Nijyuuni': '/shows/nanabun-no-nijyuuni',
        'Ishuzoku Reviewers': '/shows/ishuzoku-reviewers',
        'Boku no Tonari ni Ankoku Hakaishin ga Imasu': '/shows/boku-no-tonari-ni-ankoku-hakaishin-ga-imasu',
        'Cardfight!! Vanguard - Zoku Koukousei-hen': '/shows/cardfight-vanguard-zoku-koukousei-hen',
        'Detective Conan': '/shows/detective-conan',
        'Boku no Hero Academia': '/shows/boku-no-hero-academia',
        'Runway de Waratte': '/shows/runway-de-waratte',
    }


def mock(responses: RequestsMock, url: str, html: str) -> None:
    responses.add('GET', url + '&nextid=0', body=load_html(html))
    responses.add(
        'GET', url + '&nextid=1', body='There are no batches for this show yet'
    )


def magnet_link(torrent_hash):
    return f'magnet:?xt=urn:btih:{torrent_hash}&tr=udp://tracker.coppersurfer.tk:6969/announce&tr=udp://tracker.internetwarriors.net:1337/announce&tr=udp://tracker.leechersparadise.org:6969/announce&tr=udp://tracker.opentrackr.org:1337/announce&tr=udp://open.stealth.si:80/announce&tr=udp://p4p.arenabg.com:1337/announce&tr=udp://mgtracker.org:6969/announce&tr=udp://tracker.tiny-vps.com:6969/announce&tr=udp://peerfect.org:6969/announce&tr=http://share.camoe.cn:8080/announce&tr=http://t.nyaatracker.com:80/announce&tr=https://open.kickasstracker.com:443/announce'


def test_get_downloads(responses):
    mock(
        responses,
        'https://horriblesubs.info/api.php?method=getshows&type=batch&showid=1',
        'results.html',
    )

    batches = list(get_downloads(1, HorriblesubsDownloadType.BATCH))

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


def test_get_downloads_single(responses: RequestsMock, snapshot):
    mock(
        responses,
        'https://horriblesubs.info/api.php?method=getshows&type=show&showid=1',
        'show.html',
    )

    magnets = list(get_downloads(1, HorriblesubsDownloadType.SHOW))

    snapshot.assert_match(magnets)


def test_provider(responses: RequestsMock, snapshot):
    mock(
        responses,
        'https://horriblesubs.info/api.php?method=getshows&type=show&showid=264',
        'show.html',
    )
    responses.add('GET', 'https://horriblesubs.info/shows/', load_html('shows.html'))
    responses.add(
        'GET',
        'https://horriblesubs.info/shows/little-busters',
        load_html('show_page.html'),
    )
    responses.add(
        'GET',
        'https://api.jikan.moe/v3/search/anime',
        json={'results': [{'title': 'Little Busters!', 'mal_id': '12345'}]},
    )
    responses.add(
        'GET',
        'https://api.jikan.moe/v3/anime/12345',
        json={
            'title': 'Little Busters!',
            'title_synonyms': ['Busters that are little'],
        },
    )
    themoviedb(responses, '/tv/1', {'name': 'Little Busters!'})

    results = list(map(asdict, HorriblesubsProvider().search_for_tv(None, 1, 1, 2)))

    snapshot.assert_match(results)
