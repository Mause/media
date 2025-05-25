import re
from collections.abc import AsyncGenerator
from enum import Enum
from functools import lru_cache
from itertools import chain

from aiohttp import ClientSession
from cachetools import TTLCache
from lxml.html import fromstring

from ..jikan import closeness, get_names
from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..tmdb import get_tv
from ..types import ImdbId, TmdbId
from ..utils import cached
from .abc import TvProvider, tv_convert

SHOWID_RE = re.compile(r'var hs_showid = (\d+);')
ROOT = 'https://horriblesubs.info/'


def make_session():
    return ClientSession(base_url=ROOT)


class HorriblesubsDownloadType(Enum):
    SHOW = 'show'
    BATCH = 'batch'


@cached(TTLCache(128, 600))
async def get_all_shows() -> dict[str, str]:
    async with make_session() as session:
        res = await session.get('/shows/')
        res.raise_for_status()
        text = await res.text()
        shows = fromstring(text)
        shows = shows.xpath('.//div[@class="ind-show"]/a')

        return {show.attrib['title']: show.attrib['href'] for show in shows}


@lru_cache
async def get_show_id(path: str) -> int | None:
    async with make_session() as session:
        res = await session.get(path)
        res.raise_for_status()
        html = await res.text()
        m = SHOWID_RE.search(html)
        return int(m.group(1)) if m else None


def parse(html) -> dict[str, str]:
    def process(li) -> tuple[str, str]:
        line = ' '.join(line.strip('- \n') for line in li.xpath('./a/text()')).strip()
        return (
            ' '.join(map(str.strip, line.splitlines())),
            li.xpath('.//a/@href')[0].split('#')[0],
        )

    return dict(process(li) for li in html.xpath('./li'))


async def get_latest():
    async with make_session() as session:
        r = await session.get('/api.php', params={'method': 'getlatest'})
        html = fromstring(await r.text())
        return parse(html)


async def get_downloads(showid: int, type: HorriblesubsDownloadType):
    page = 0
    while True:
        downloads = list(await _get_downloads(showid, type, page))
        if downloads:
            for d in downloads:
                yield d
            page += 1
        else:
            break


async def _get_downloads(showid: int, type: HorriblesubsDownloadType, page: int):
    def process(div):
        def fn(res: str):
            t = div.xpath(
                f'.//div[contains(@class, "link-{res}")]/span/a[@title="Magnet'
                ' Link"]/@href'
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

    async with make_session() as session:
        r = await session.get(
            '/api.php',
            params={
                'method': 'getshows',
                'type': type.value,
                'showid': showid,
                'nextid': page,
            },
        )
        text = await r.text()
        if text.strip() == 'There are no batches for this show yet':
            return ()

    html = fromstring(text)

    if html.attrib.get('class') == 'rls-info-container':
        torrents = [html]
    else:
        torrents = html.xpath('.//div[contains(@class, "rls-info-container")]')
    return chain.from_iterable(process(div) for div in torrents)


async def search(showid: int, search_term: str):
    async with make_session() as session:
        await session.get(
            'api.php',
            params={
                'method': 'getshows',
                'type': 'show',
                'mode': 'filter',
                'showid': showid,
                'value': search_term,
            },
        )


async def search_for_tv(tmdb_id: TmdbId, season: int, episode: int | None = None):
    if season != 1:
        return

    shows = await get_all_shows()

    names = await get_names(tmdb_id)

    show = max(shows.keys(), key=lambda key: closeness(key, names) > 95)
    if closeness(show, names) < 95:
        return

    show_id = await get_show_id(shows[show])
    if not show_id:
        return

    async for item in get_downloads(show_id, HorriblesubsDownloadType.SHOW):
        if episode is None or item['episode'] == f'{episode:02d}':
            yield item


class HorriblesubsProvider(TvProvider):
    type = ProviderSource.HORRIBLESUBS

    async def search_for_tv(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
        season: int,
        episode: int | None = None,
    ) -> AsyncGenerator[ITorrent, None]:
        name = (await get_tv(tmdb_id)).name
        template = f'HorribleSubs {name} S{season:02d}'

        async for item in search_for_tv(tmdb_id, season, episode):
            yield ITorrent(
                source=ProviderSource.HORRIBLESUBS,
                title=f'{template}E{int(item["episode"], 10):02d} {item["resolution"]}',
                seeders=0,
                download=item['download'],
                category=tv_convert(item['resolution']),
                episode_info=EpisodeInfo(seasonnum=season, epnum=item['episode']),
            )

    async def health(self):
        return await self.check_http(ROOT)


async def main():
    print(list(await search_for_tv('95550', 1, 1)))


if __name__ == '__main__':
    import uvloop

    uvloop.run(main())
