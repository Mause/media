import re
from enum import Enum
from functools import lru_cache
from typing import Dict, Optional, Tuple

from cachetools.func import ttl_cache
from lxml.html import fromstring
from requests_toolbelt.sessions import BaseUrlSession

session = BaseUrlSession('https://horriblesubs.info/')

SHOWID_RE = re.compile(r'var hs_showid = (\d+);')


class HorriblesubsDownloadType(Enum):
    SHOW = 'show'
    BATCH = 'batch'


@ttl_cache()
def get_all_shows() -> Dict[str, str]:
    shows = fromstring(session.get('/shows/').content)
    shows = shows.xpath('.//div[@class="ind-show"]/a')

    return {show.attrib['title']: show.attrib['href'] for show in shows}


@lru_cache()
def get_show_id(path: str) -> Optional[str]:
    html = session.get(path).text
    m = SHOWID_RE.search(html)
    return m.group(1) if m else None


def parse(html) -> Dict[str, str]:
    def process(li) -> Tuple[str, str]:
        line = ' '.join(line.strip('- \n') for line in li.xpath('./a/text()')).strip()
        return (
            ' '.join(map(str.strip, line.splitlines())),
            li.xpath('.//a/@href')[0].split('#')[0],
        )

    return dict(process(li) for li in html.xpath('./li'))


def get_latest():
    r = session.get('/api.php', params={'method': 'getlatest'})
    html = fromstring(r.content)
    return parse(html)


@ttl_cache()
def get_downloads(showid: int, type: HorriblesubsDownloadType):
    def internal():
        page = 0
        while True:
            downloads = list(_get_downloads(showid, type, page))
            if downloads:
                yield from downloads
                page += 1
            else:
                break

    return dict(internal())


def _get_downloads(showid: int, type: HorriblesubsDownloadType, page: int):
    def process(div):
        ten_eighty = div.xpath(
            './/div[contains(@class, "link-1080p")]/span/a[@title="Magnet Link"]/@href'
        )
        assert len(ten_eighty) == 1, ten_eighty
        return div.attrib['id'], ten_eighty[0]

    r = session.get(
        '/api.php',
        params={
            'method': 'getshows',
            'type': type.name,
            'showid': showid,
            'nextid': page,
        },
    )
    html = fromstring(r.content)

    torrents = html.xpath('.//div[contains(@class, "rls-info-container")]')
    return (process(div) for div in torrents)


def search(showid: int, search_term: str):
    session.get(
        'api.php',
        params={
            'method': 'getshows',
            'type': 'show',
            'mode': 'filter',
            'showid': showid,
            'value': search_term,
        },
    )
