from pathlib import Path

from responses import RequestsMock

from ..horriblesubs import HorriblesubsDownloadType, get_downloads, get_latest


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


def test_get_downloads_single(responses: RequestsMock):
    mock(
        responses,
        'https://horriblesubs.info/api.php?method=getshows&type=show&showid=1',
        'show.html',
    )

    magnets = list(get_downloads(1, HorriblesubsDownloadType.SHOW))
    assert magnets == [
        # '01': m('magnet'),  # test data is missing this one
        {
            'episode': '02',
            'download': magnet_link('VSBAG4BJNDVDWI2GLWOQ3UYIJAFI35Y6'),
            'resolution': '1080',
        },
        {
            'episode': '03',
            'download': magnet_link('PZMGSAST532KUYJ2LYR7PEEHNTP6E5FU'),
            'resolution': '1080',
        },
        {
            'episode': '04',
            'download': magnet_link('JX2JEXQ4XPYZBE4VOE7RBY2IQMGDIUME'),
            'resolution': '1080',
        },
        {
            'episode': '05',
            'download': magnet_link('RFZF4JPSNNAERZZEOXVUEJGZVPOUVPVO'),
            'resolution': '1080',
        },
        {
            'episode': '06',
            'download': magnet_link('B3IR74HLUAVMVKPS6HD3K2DJKJSTRY2F'),
            'resolution': '1080',
        },
        {
            'episode': '07',
            'download': magnet_link('MQMIBASXNTVLVBQ5AAHTDNFUGWXEAP7B'),
            'resolution': '1080',
        },
        {
            'episode': '08',
            'download': magnet_link('RLQFPJ6AZD44E65VFIRW6RIO3GPPMDD6'),
            'resolution': '1080',
        },
        {
            'episode': '09',
            'download': magnet_link('SXDC7L2CAMC5KXVLKNUWOCP4CZQ7HHFC'),
            'resolution': '1080',
        },
        {
            'episode': '10',
            'download': magnet_link('E7I3GTBL6NUBAUZYUL7PRZDG6J2SPRF7'),
            'resolution': '1080',
        },
        {
            'episode': '11',
            'download': magnet_link('ANBB2EMKEPST3FTCHCZ3OBVS557REHXW'),
            'resolution': '1080',
        },
        {
            'episode': '12',
            'download': magnet_link('5QRG6LYP3FZALFH4MYQTVVFP63XMQ4WX'),
            'resolution': '1080',
        },
    ]
