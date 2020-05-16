import re
from enum import Enum
from functools import lru_cache
from itertools import chain
from typing import Dict, Optional, Set, Tuple

from cachetools.func import ttl_cache
from fuzzywuzzy import fuzz
from lxml.html import fromstring
from requests_toolbelt.sessions import BaseUrlSession

from .tmdb import get_tv

session = BaseUrlSession('https://horriblesubs.info/')
jikan = BaseUrlSession('https://api.jikan.moe/v3/')

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


def get_downloads(showid: int, type: HorriblesubsDownloadType):
    page = 0
    while True:
        downloads = list(_get_downloads(showid, type, page))
        if downloads:
            yield from downloads
            page += 1
        else:
            break


def _get_downloads(showid: int, type: HorriblesubsDownloadType, page: int):
    def process(div):
        def fn(res: str):
            t = div.xpath(
                f'.//div[contains(@class, "link-{res}")]/span/a[@title="Magnet Link"]/@href'
            )
            return t[0] if t else None

        return [
            {
                'episode': div.attrib['id'],
                'resolution': resolution,
                'download': fn(resolution),
            }
            for resolution in ('1080', '720', '480')
            if fn(resolution)
        ]

    r = session.get(
        '/api.php',
        params={
            'method': 'getshows',
            'type': type.value,
            'showid': showid,
            'nextid': page,
        },
    )
    if r.text.strip() == 'There are no batches for this show yet':
        return ()

    html = fromstring(r.content)

    if html.attrib.get('class') == 'rls-info-container':
        torrents = [html]
    else:
        torrents = html.xpath('.//div[contains(@class, "rls-info-container")]')
    return chain.from_iterable(process(div) for div in torrents)


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


@ttl_cache()
def get_names(tmdb_id: int) -> Set[str]:
    tv = get_tv(tmdb_id)
    results = jikan.get('search/anime', params={'q': tv['name'], 'limit': 1}).json()[
        'results'
    ]
    result = jikan.get(f'anime/{results[0]["mal_id"]}').json()

    return set([tv['name'], result['title']] + result['title_synonyms'])


def search_for_tv(tmdb_id, season, episode):
    if season != 1:
        return []

    shows = get_all_shows()

    names = get_names(tmdb_id)

    closeness = lambda key: max(fuzz.ratio(key.lower(), name.lower()) for name in names)

    show = max(shows.keys(), key=lambda key: closeness(key) > 95)
    if closeness(show) < 95:
        return []

    show_id = get_show_id(shows[show])

    results = get_downloads(show_id, HorriblesubsDownloadType.SHOW)
    if episode is None:
        return results
    else:
        return (item for item in results if item['episode'] == f'{episode:02d}')


if __name__ == '__main__':
    print(list(search_for_tv('95550', 1, 1)))
