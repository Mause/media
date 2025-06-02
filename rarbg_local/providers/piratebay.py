import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlencode

import aiohttp

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..types import ImdbId, TmdbId
from .abc import MovieProvider, TvProvider, format

logger = logging.getLogger(__name__)

categories = {
    'audio': {
        'music': 101,
        'audio_books': 102,
        'sound_clips': 103,
        'FLAC': 104,
        'other': 199,
    },
    'video': {
        'movies': 201,
        'movies_dvdr': 202,
        'music_videos': 203,
        'movie_clips': 204,
        'tv_shows': 205,
        'handheld': 206,
        'hd_movies': 207,
        'hd_tv_shows': 208,
        '3d': 209,
        'other': 299,
    },
}


def convert_category(category: int):
    for broad, subcats in categories.items():
        for subcat, cat in subcats.items():
            if category == cat:
                return f'{broad} - {subcat}'.replace('_', ' ').title()

    message = f'unrecognised category: {category}'
    logger.warn(message)
    return message


def magnet(info_hash: str, name: str) -> str:
    """Generate a magnet link from an info hash."""
    return f'magnet:?xt=urn:btih:{info_hash}&' + urlencode({'dn': name})


class PirateBayProvider(TvProvider, MovieProvider):
    type = ProviderSource.PIRATEBAY
    root = 'https://apibay.org/q.php'

    @asynccontextmanager
    async def search(self, q: str) -> AsyncGenerator[list[dict[str, str]]]:
        async with (
            aiohttp.ClientSession() as session,
            await session.get(self.root, params={'q': q}) as resp,
        ):
            resp.raise_for_status()
            data = await resp.json()

            if len(data) == 1 and data[0]['name'] == 'No results returned':
                return

            yield data

    async def search_for_tv(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
        season: int,
        episode: int | None = None,
    ) -> AsyncGenerator[ITorrent, None]:
        async with self.search(imdb_id + ' ' + format(season, episode)) as data:
            for item in data:
                yield ITorrent(
                    source=ProviderSource.PIRATEBAY,
                    title=item['name'],
                    seeders=int(item['seeders']),
                    download=magnet(item['info_hash'], item['name']),
                    category=convert_category(int(item['category'])),
                    episode_info=EpisodeInfo(seasonnum=season, epnum=episode),
                )

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        async with self.search(imdb_id) as data:
            for item in data:
                yield ITorrent(
                    source=ProviderSource.PIRATEBAY,
                    title=item['name'],
                    seeders=int(item['seeders']),
                    download=magnet(item['info_hash'], item['name']),
                    category=convert_category(int(item['category'])),
                )

    async def health(self):
        return await self.check_http(self.root)
