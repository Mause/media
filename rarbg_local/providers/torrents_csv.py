from collections.abc import AsyncGenerator

import aiohttp

from ..models import ITorrent, ProviderSource
from ..utils import ImdbId, TmdbId
from .abc import MovieProvider, TvProvider, format


class TorrentsCsvProvider(MovieProvider, TvProvider):
    type = ProviderSource.TORRENTS_CSV
    root = 'https://torrents-csv.com'

    async def query(self, q: str):
        async with aiohttp.ClientSession() as session:
            res = await session.get(self.root + "/service/search", params={"q": q})
            res.raise_for_status()
            return (await res.json())['torrents']

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        for item in await self.query(imdb_id):
            yield ITorrent(
                source=ProviderSource.TORRENTS_CSV,
                title=item['name'],
                seeders=item['seeders'],
                download=item['infohash'],
                category=item['category'],
            )

    async def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int | None = None
    ) -> AsyncGenerator[ITorrent, None]:
        for item in await self.query(f"{imdb_id} {format(season, episode)}"):
            yield ITorrent(
                source=ProviderSource.TORRENTS_CSV,
                title=item['name'],
                seeders=item['seeders'],
                download=item['infohash'],
                category=item['category'],
            )

    async def health(self):
        return await self.check_http(self.root)
