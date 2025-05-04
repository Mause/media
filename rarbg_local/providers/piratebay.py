from typing import AsyncGenerator, Optional

import aiohttp

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..types import ImdbId, TmdbId
from .abc import MovieProvider, TvProvider, format, movie_convert, tv_convert


class PirateBayProvider(TvProvider, MovieProvider):
    name = 'piratebay'
    root = 'https://apibay.org'

    async def search_for_tv(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
        season: int,
        episode: Optional[int] = None,
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
                    download=item['info_hash'],
                    category=tv_convert(item['category']),
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
                    download=item['info_hash'],
                    category=movie_convert(item['category']),
                )
