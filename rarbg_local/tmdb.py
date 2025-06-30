import os
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Any, Literal

import aiohttp
import aiohttp.web_exceptions
import backoff
from cachetools import LRUCache, TTLCache
from pydantic import BaseModel, Field, model_validator

from .models import (
    MediaType,
    MovieResponse,
    SearchResponse,
    TvApiResponse,
    TvSeasonResponse,
)
from .types import ImdbId, TmdbId
from .utils import cached

base = 'https://api.themoviedb.org/3/'

ThingType = Literal['movie', 'tv']


@backoff.on_exception(
    backoff.fibo,
    aiohttp.web_exceptions.HTTPException,
    max_tries=5,
    giveup=lambda e: not isinstance(e, aiohttp.web_exceptions.HTTPTooManyRequests),
)
async def get_json[TBaseModel: BaseModel](
    path: str, hydrate: type[TBaseModel], **kwargs: Any
) -> TBaseModel:
    access_token = (
        'access_token'
        if 'PYTEST_CURRENT_TEST' in os.environ
        else os.environ['TMDB_READ_ACCESS_TOKEN']
    )
    async with aiohttp.ClientSession(
        base_url=base,
        headers={
            'Authorization': f'Bearer {access_token}',
        },
    ) as tmdb:
        r = await tmdb.get(path, **kwargs)
        r.raise_for_status()
        return hydrate.model_validate(await r.json())


class EmptyStringAsNoneModel(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none[T](cls, data: T) -> T | dict:
        if isinstance(data, dict):
            return {k: (None if v == '' else v) for k, v in data.items()}
        return data


class SearchBaseResponse(BaseModel):
    class TvSearch(EmptyStringAsNoneModel):
        media_type: Literal['tv']
        id: TmdbId
        name: str
        first_air_date: datetime | None = None

    class MovieSearch(EmptyStringAsNoneModel):
        media_type: Literal['movie']
        id: TmdbId
        title: str
        release_date: datetime | None = None

    class PersonSearch(BaseModel):
        media_type: Literal['person']
        id: TmdbId

    results: Annotated[
        list[TvSearch | MovieSearch | PersonSearch], Field(default_factory=list)
    ]


SearchItem = SearchBaseResponse.TvSearch | SearchBaseResponse.MovieSearch


def get_year(result: SearchItem) -> int | None:
    dt = None
    if isinstance(result, SearchBaseResponse.TvSearch):
        dt = result.first_air_date
    elif isinstance(result, SearchBaseResponse.MovieSearch):
        dt = result.release_date

    return dt.year if dt else None


def get_title(result: SearchItem) -> str:
    return (
        result.name if isinstance(result, SearchBaseResponse.TvSearch) else result.title
    )


@cached(TTLCache(1024, 360))
async def search_themoviedb(s: str) -> list[SearchResponse]:
    MAP = {'tv': MediaType.SERIES, 'movie': MediaType.MOVIE}
    r = await get_json('search/multi', SearchBaseResponse, params={'query': s})
    return [
        SearchResponse(
            type=MAP[result.media_type],
            title=get_title(result),
            year=get_year(result),
            tmdb_id=result.id,
        )
        for result in r.results
        if isinstance(
            result, (SearchBaseResponse.TvSearch, SearchBaseResponse.MovieSearch)
        )
    ]


@cached(LRUCache(256))
async def get_movie(id: TmdbId) -> MovieResponse:
    return await get_json(f'movie/{id}', MovieResponse)


@cached(TTLCache(256, 360))
async def get_tv(id: TmdbId) -> TvApiResponse:
    return await get_json(f'tv/{id}', TvApiResponse)


async def get_movie_imdb_id(movie_id: TmdbId) -> ImdbId:
    return await get_imdb_id('movie', movie_id)


async def get_tv_imdb_id(tv_id: TmdbId) -> ImdbId:
    return await get_imdb_id('tv', tv_id)


class ExternalIds(BaseModel):
    imdb_id: ImdbId


@cached(LRUCache(360))
async def get_tv_episode_imdb_id(tmdb_id: TmdbId, season: int, episode: int) -> ImdbId:
    return (
        await get_json(
            f'tv/{tmdb_id}/season/{season}/episode/{episode}/external_ids',
            ExternalIds,
        )
    ).imdb_id


@cached(LRUCache(360))
async def get_imdb_id(type: ThingType, id: TmdbId) -> ImdbId:
    return (await get_json(f'{type}/{id}/external_ids', ExternalIds)).imdb_id


@cached(TTLCache(256, 360))
async def get_tv_episodes(id: TmdbId, season: int) -> TvSeasonResponse:
    return await get_json(f'tv/{id}/season/{season}', TvSeasonResponse)


class ReleaseType(Enum):
    PREMIERE = 1
    THEATRICAL_LIMITED = 2
    THEATRICAL = 3
    DIGITAL = 4
    PHYSICAL = 5
    TV = 6


class Discover(BaseModel):
    class DiscoverMovie(BaseModel):
        id: TmdbId
        title: str
        release_date: datetime | None = None
        poster_path: str | None = None
        backdrop_path: str | None = None
        overview: str | None = None

    page: int
    results: list[DiscoverMovie]
    total_pages: int
    total_results: int


async def discover(
    types: tuple[ReleaseType, ...] = (ReleaseType.PHYSICAL, ReleaseType.DIGITAL),
) -> Discover:
    return await get_json(
        'discover/movie',
        Discover,
        params={
            'sort_by': ','.join(('popularity.desc', 'primary_release_date.desc')),
            'primary_release_date.lte': date.today().isoformat(),
            'with_release_type': '|'.join(str(ReleaseType(i).value) for i in types),
        },
    )
