from collections.abc import AsyncGenerator
from urllib.parse import urlencode

import aiohttp

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..utils import ImdbId, TmdbId
from .abc import MovieProvider, TvProvider, format

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


def magnet(info_hash: str, name: str) -> str:
    """Generate a magnet link from an info hash."""
    return f'magnet:?xt=urn:btih:{info_hash}&' + urlencode({'dn': name})


class PirateBayProvider(TvProvider, MovieProvider):
    type = ProviderSource.PIRATEBAY
    root = 'https://apibay.org'

    async def search_for_tv(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
        season: int,
        episode: int | None = None,
    ) -> AsyncGenerator[ITorrent, None]:
        async with (
            aiohttp.ClientSession() as session,
            await session.get(
                self.root + '/q.php',
                params={'q': imdb_id + ' ' + format(season, episode)},
            ) as resp,
        ):
            data = await resp.json()

            if len(data) == 1 and data[0]['name'] == 'No results returned':
                return

            for item in data:
                yield ITorrent(
                    source=ProviderSource.PIRATEBAY,
                    title=item['name'],
                    seeders=item['seeders'],
                    download=magnet(item['info_hash'], item['name']),
                    category=convert_category(item['category']),
                    episode_info=EpisodeInfo(seasonnum=season, epnum=episode),
                )

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        async with (
            aiohttp.ClientSession() as session,
            await session.get(self.root + '/q.php', params={'q': imdb_id}) as resp,
        ):
            data = await resp.json()

            if len(data) == 1 and data[0]['name'] == 'No results returned':
                return

            for item in data:
                yield ITorrent(
                    source=ProviderSource.PIRATEBAY,
                    title=item['name'],
                    seeders=item['seeders'],
                    download=magnet(item['info_hash'], item['name']),
                    category=convert_category(item['category']),
                )
