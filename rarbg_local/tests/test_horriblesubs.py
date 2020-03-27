from pathlib import Path

from pytest import mark

from ..horriblesubs import get_downloads, get_latest

pytestmark = mark.skip


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


def test_get_downloads(responses):
    responses.add(
        'GET',
        'https://horriblesubs.info/api.php?method=getshows&type=batch&showid=1',
        body=load_html('results.html'),
    )

    batches = get_downloads(1, 'batch')

    assert batches == {
        "": "magnet:"
        + "?xt=urn:btih:2UIBW66DGKSND7QKUBFE5WOGS2SCY2ZE"
        + "&tr=udp://tracker.coppersurfer.tk:6969/announce"
        + "&tr=udp://tracker.internetwarriors.net:1337/announce"
        + "&tr=udp://tracker.leechersparadise.org:6969/announce"
        + "&tr=udp://tracker.opentrackr.org:1337/announce"
        + "&tr=udp://open.stealth.si:80/announce"
        + "&tr=udp://p4p.arenabg.com:1337/announce"
        + "&tr=udp://mgtracker.org:6969/announce"
        + "&tr=udp://tracker.tiny-vps.com:6969/announce"
        + "&tr=udp://peerfect.org:6969/announce"
        + "&tr=http://share.camoe.cn:8080/announce"
        + "&tr=http://t.nyaatracker.com:80/announce"
        + "&tr=https://open.kickasstracker.com:443/announce"
    }


def test_get_downloads_single(responses):
    responses.add(
        'GET',
        'https://horriblesubs.info/api.php?method=getshows&type=show&showid=1',
        body=load_html('show.html'),
    )

    magnets = get_downloads(1, 'show')

    m = (
        lambda torrent_hash: f'magnet:?xt=urn:btih:{torrent_hash}&tr=udp://tracker.coppersurfer.tk:6969/announce&tr=udp://tracker.internetwarriors.net:1337/announce&tr=udp://tracker.leechersparadise.org:6969/announce&tr=udp://tracker.opentrackr.org:1337/announce&tr=udp://open.stealth.si:80/announce&tr=udp://p4p.arenabg.com:1337/announce&tr=udp://mgtracker.org:6969/announce&tr=udp://tracker.tiny-vps.com:6969/announce&tr=udp://peerfect.org:6969/announce&tr=http://share.camoe.cn:8080/announce&tr=http://t.nyaatracker.com:80/announce&tr=https://open.kickasstracker.com:443/announce'
    )

    assert magnets == {
        # '01': m('magnet'),  # test data is missing this one
        '02': m('VSBAG4BJNDVDWI2GLWOQ3UYIJAFI35Y6'),
        '03': m('PZMGSAST532KUYJ2LYR7PEEHNTP6E5FU'),
        '04': m('JX2JEXQ4XPYZBE4VOE7RBY2IQMGDIUME'),
        '05': m('RFZF4JPSNNAERZZEOXVUEJGZVPOUVPVO'),
        '06': m('B3IR74HLUAVMVKPS6HD3K2DJKJSTRY2F'),
        '07': m('MQMIBASXNTVLVBQ5AAHTDNFUGWXEAP7B'),
        '08': m('RLQFPJ6AZD44E65VFIRW6RIO3GPPMDD6'),
        '09': m('SXDC7L2CAMC5KXVLKNUWOCP4CZQ7HHFC'),
        '10': m('E7I3GTBL6NUBAUZYUL7PRZDG6J2SPRF7'),
        '11': m('ANBB2EMKEPST3FTCHCZ3OBVS557REHXW'),
        '12': m('5QRG6LYP3FZALFH4MYQTVVFP63XMQ4WX'),
    }
