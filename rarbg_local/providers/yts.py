from collections.abc import AsyncGenerator

import aiohttp
from healthcheck import HealthcheckCallbackResponse
from pydantic import BaseModel

from ..models import ITorrent, ProviderSource
from ..types import ImdbId, TmdbId
from .abc import MovieProvider


class YtsTorrent(BaseModel):
    hash: str
    quality: str
    video_codec: str
    seeds: int


class Movie(BaseModel):
    id: int
    title: str
    torrents: list[YtsTorrent]


class MovieResponse(BaseModel):
    movie_count: int
    limit: int
    page_number: int
    movies: list[Movie]


class Response(BaseModel):
    data: MovieResponse


class YtsProvider(MovieProvider):
    base = 'https://movies-api.accel.li/api/v2'
    type = ProviderSource.YTS

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        async with aiohttp.ClientSession() as session:
            res = await session.get(
                self.base + '/list_movies.json',
                params={
                    'query_term': imdb_id,
                },
            )
            js = Response.model_validate(await res.json())
            for item in js.data.movies:
                for torrent in item.torrents:
                    yield ITorrent(
                        source=ProviderSource.YTS,
                        category=torrent.quality,
                        download='magnet:' + torrent.hash,
                        title=item.title
                        + ' '
                        + torrent.quality
                        + ' '
                        + torrent.video_codec,
                        seeders=torrent.seeds,
                    )

    async def health(self) -> HealthcheckCallbackResponse:
        return await self.check_http(self.base)
