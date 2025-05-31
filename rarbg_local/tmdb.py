import os
from datetime import date
from enum import Enum
from itertools import chain
from typing import Literal

import aiohttp
import aiohttp.web_exceptions
import backoff
from cachetools import LRUCache, TTLCache

from .models import (
    MediaType,
    MovieResponse,
    SearchResponse,
    TvApiResponse,
    TvSeasonResponse,
)
from .types import ImdbId, TmdbId
from .utils import cached, precondition

base = 'https://api.themoviedb.org/3/'

ThingType = Literal['movie', 'tv']


def try_(dic: dict[str, str], *keys: str) -> str | None:
    return next((dic[key] for key in keys if key in dic), None)


@backoff.on_exception(
    backoff.fibo,
    aiohttp.web_exceptions.HTTPException,
    max_tries=5,
    giveup=lambda e: not isinstance(e, aiohttp.web_exceptions.HTTPTooManyRequests),
)
async def get_json(path, **kwargs):
    access_token = os.environ['TMDB_READ_ACCESS_TOKEN']
    async with aiohttp.ClientSession(
        base_url=base,
        headers={
            'Authorization': f'Bearer {access_token}',
        },
    ) as tmdb:
        r = await tmdb.get(path, **kwargs)
        r.raise_for_status()
        return await r.json()


@cached(LRUCache(360))
async def get_configuration() -> dict:
    return await get_json('configuration')


def get_year(result: dict[str, str]) -> int | None:
    data = try_(result, 'first_air_date', 'release_date')
    return date.fromisoformat(data).year if data else None


@cached(TTLCache(1024, 360))
async def search_themoviedb(s: str) -> list[SearchResponse]:
    MAP = {'tv': MediaType.SERIES, 'movie': MediaType.MOVIE}
    r = await get_json('search/multi', params={'query': s})
    return [
        SearchResponse(
            type=MAP[result['media_type']],
            title=try_(result, 'title', 'name'),
            year=get_year(result),
            tmdb_id=result['id'],
        )
        for result in r.get('results', [])
        if result['media_type'] in MAP
    ]


@cached(TTLCache(1024, 360))
async def find_themoviedb(imdb_id: ImdbId) -> dict[str, str]:
    precondition(imdb_id.startswith('tt'), 'Invalid imdb_id')
    results = await get_json(f'find/{imdb_id}', params={'external_source': 'imdb_id'})

    result = next(item for item in chain.from_iterable(results.values()))

    return {**result, 'title': result['original_name']}


@cached(LRUCache(1024))
async def resolve_id(imdb_id: ImdbId, type: ThingType) -> TmdbId:
    precondition(imdb_id.startswith('tt'), 'Invalid imdb_id')
    results = await get_json(f'find/{imdb_id}', params={'external_source': 'imdb_id'})

    res = results[f'{type}_results']
    precondition(res, f'No results for {imdb_id} as a {type}')

    return res[0]['id']


@cached(LRUCache(256))
async def get_movie(id: TmdbId) -> MovieResponse:
    return MovieResponse.model_validate(await get_json(f'movie/{id}'))


@cached(TTLCache(256, 360))
async def get_tv(id: TmdbId) -> TvApiResponse:
    return TvApiResponse.model_validate(await get_json(f'tv/{id}'))


async def get_movie_imdb_id(movie_id: TmdbId) -> ImdbId:
    return await get_imdb_id('movie', movie_id)


async def get_tv_imdb_id(tv_id: TmdbId) -> ImdbId:
    return await get_imdb_id('tv', tv_id)


@cached(LRUCache(360))
async def get_imdb_id(type: ThingType, id: TmdbId) -> ImdbId:
    return (await get_json(f'{type}/{id}/external_ids'))['imdb_id']


@cached(TTLCache(256, 360))
async def get_tv_episodes(id: TmdbId, season: int) -> TvSeasonResponse:
    return TvSeasonResponse.model_validate(await get_json(f'tv/{id}/season/{season}'))


class ReleaseType(Enum):
    PREMIERE = 1
    THEATRICAL_LIMITED = 2
    THEATRICAL = 3
    DIGITAL = 4
    PHYSICAL = 5
    TV = 6


async def discover(types=(ReleaseType.PHYSICAL, ReleaseType.DIGITAL)):
    return await get_json(
        'discover/movie',
        params={
            'sort_by': ','.join(('popularity.desc', 'primary_release_date.desc')),
            'primary_release_date.lte': date.today().isoformat(),
            'with_release_type': '|'.join(str(ReleaseType(i).value) for i in types),
        },
    )
