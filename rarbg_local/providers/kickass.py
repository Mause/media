import logging
import re
import string
from collections.abc import AsyncGenerator
from typing import Any

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..tmdb import get_movie, get_tv
from ..types import ImdbId, TmdbId
from .abc import MovieProvider, TvProvider, movie_convert, tv_convert

logger = logging.getLogger(__name__)
ROOT = 'https://katcr.co'


def is_node(node):
    return node


async def fetch(url: str) -> AsyncGenerator[dict[str, Any], None]:
    async with ClientSession(base_url=ROOT) as session:
        try:
            r = await session.get(url)
        except ConnectionError:
            logger.exception('Failed to reach kickass')
            return

        soup = BeautifulSoup(await r.read(), "lxml")

    for i in soup.find_all(
        'div', {'class': 'tab_content', 'id': lambda id: id != 'comments'}
    ):
        resolution = is_node(i).attrs['id']

        table = is_node(is_node(i).find('table'))
        tbody = is_node(table.find('tbody'))

        for row in tbody.find_all('tr'):
            magnet = row.find('a', href=lambda href: href.startswith("magnet:")).attrs[
                'href'
            ]
            title = row.find('a', {'class': 'torrents_table__torrent_title'}).text

            yield {
                'title': title.strip(),
                'magnet': magnet,
                'resolution': resolution,
                'seeders': int(
                    row.find('td', {'data-title': "Seed"}).text.replace(',', '')
                ),
            }


def tokenise(name: str) -> str:
    name = name.lower()
    name = re.sub(f'[{string.punctuation}]', '', name)
    name = name.replace(' ', '-')

    return name


async def search_for_tv(
    imdb_id: ImdbId, tmdb_id: TmdbId, season: int, episode: int | None = None
) -> AsyncGenerator[dict, None]:
    name = (await get_tv(tmdb_id)).name

    if episode is None:
        key = f'S{season:02d}'
        async for item in base(name, imdb_id):
            if key in item['title']:
                yield item
    else:
        async for item in fetch(
            f'/name/search/{tokenise(name)}/i{imdb_id.lstrip("t")}/{season}/{episode}'
        ):
            yield item


def base(name: str, imdb_id: ImdbId):
    return fetch(f'/name/{tokenise(name)}/i{imdb_id.lstrip("t")}')


async def search_for_movie(imdb_id: ImdbId, tmdb_id: TmdbId):
    name = (await get_movie(tmdb_id)).title

    async for item in base(name, imdb_id):
        yield item


class KickassProvider(TvProvider, MovieProvider):
    type = ProviderSource.KICKASS

    async def search_for_tv(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
        season: int,
        episode: int | None = None,
    ) -> AsyncGenerator[ITorrent, None]:
        if not imdb_id:
            return

        async for item in search_for_tv(imdb_id, tmdb_id, season, episode):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=tv_convert(item['resolution']),
                episode_info=EpisodeInfo(seasonnum=season, epnum=episode),
            )

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        async for item in search_for_movie(imdb_id, tmdb_id):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=movie_convert(item['resolution']),
            )

    async def health(self):
        return await self.check_http(ROOT)
