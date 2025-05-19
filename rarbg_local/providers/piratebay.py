from collections.abc import AsyncGenerator
from urllib.parse import urlencode

import aiohttp

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..types import ImdbId, TmdbId
from .abc import MovieProvider, TvProvider, format, movie_convert, tv_convert


def magnet(info_hash: str, name: str) -> str:
    """Generate a magnet link from an info hash."""
    return 'magnet:?' + urlencode({'xt': f'urn:btih:{info_hash}', 'dn': name})


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
                    download=magnet(item['info_hash'], item['name']),
                    category=movie_convert(item['category']),
                )
