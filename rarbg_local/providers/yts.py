from collections.abc import AsyncGenerator
from typing import Annotated, Literal

from aiohttp import ClientSession
from healthcheck import HealthcheckCallbackResponse
from pydantic import BaseModel, Field

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


class Meta(BaseModel):
    api_version: Literal[2]
    execution_time: str


class Response[T](BaseModel):
    data: T
    meta: Annotated[Meta, Field(alias='@meta')]


class YtsProvider(MovieProvider):
    base = 'https://movies-api.accel.li/api/v2'
    type = ProviderSource.YTS

    async def list_movies(
        self,
        session: ClientSession,
        query_term: str,
        *,
        limit: int = 20,
        page: int = 1,
        minimum_rating: int = 0,
        genre: str | None = None,
        sort_by: Literal[
            'title',
            'year',
            'rating',
            'peers',
            'seeds',
            'download_count',
            'like_count',
            'date_added',
        ] = 'date_added',
        order_by: Literal['desc', 'asc'] = 'desc',
        with_rt_ratings: bool = False,
    ) -> Response[MovieResponse]:
        res = await session.get(
            self.base + '/list_movies.json',
            params={
                k: v
                for k, v in {
                    'query_term': query_term,
                    'limit': limit,
                    'page': page,
                    'minimum_rating': minimum_rating,
                    'genre': genre,
                    'sort_by': sort_by,
                    'order_by': order_by,
                    'with_rt_ratings': with_rt_ratings,
                }.items()
                if v is not None
            },
        )
        return Response[MovieResponse].model_validate(await res.json())

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        async with ClientSession() as session:
            js = await self.list_movies(session, query_term=imdb_id)
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
