from datetime import date
from enum import Enum
from itertools import chain
from typing import Dict, List, Literal, Optional, Union

import backoff
import requests
from requests_toolbelt.sessions import BaseUrlSession

from .models import MovieResponse, SearchResponse, TvApiResponse, TvSeasonResponse
from .utils import lru_cache, precondition, ttl_cache

tmdb = BaseUrlSession('https://api.themoviedb.org/3/')
tmdb.params['api_key'] = '66b197263af60702ba14852b4ec9b143'

ThingType = Literal['movie', 'tv']


def try_(dic: Dict[str, str], *keys: str) -> Optional[str]:
    return next((dic[key] for key in keys if key in dic), None)


@backoff.on_exception(
    backoff.fibo,
    requests.exceptions.RequestException,
    max_tries=5,
    giveup=lambda e: e.response.status_code != 429,
)
def get_json(*args, **kwargs):
    r = tmdb.get(*args, **kwargs)
    r.raise_for_status()
    return r.json()


@lru_cache()
def get_configuration() -> Dict:
    return get_json('configuration')


def get_year(result: Dict[str, str]) -> Optional[int]:
    data = try_(result, 'first_air_date', 'release_date')
    return date.fromisoformat(data).year if data else None


@ttl_cache()
def search_themoviedb(s: str) -> List[SearchResponse]:
    MAP = {'tv': 'series', 'movie': 'movie'}
    r = tmdb.get('search/multi', params={'query': s})
    return [
        SearchResponse(
            type=MAP[result['media_type']],
            title=try_(result, 'title', 'name'),
            year=get_year(result),
            imdbID=result['id'],
        )
        for result in r.json().get('results', [])
        if result['media_type'] in MAP
    ]


@lru_cache()
def find_themoviedb(imdb_id: str):
    precondition(imdb_id.startswith('tt'), 'Invalid imdb_id')
    results = tmdb.get(f'find/{imdb_id}', params={'external_source': 'imdb_id'}).json()

    result = next(item for item in chain.from_iterable(results.values()))

    return dict(result, title=result['original_name'])


@lru_cache()
def resolve_id(imdb_id: str, type: ThingType) -> str:
    precondition(imdb_id.startswith('tt'), 'Invalid imdb_id')
    results = tmdb.get(f'find/{imdb_id}', params={'external_source': 'imdb_id'}).json()

    if type:
        res = results[f'{type}_results']
        precondition(res, f'No results for {imdb_id} as a {type}')
        res = res[0]
    else:
        res = next((item for item in chain.from_iterable(results.values())), None)
        precondition(res, f'No results for {imdb_id}')

    return res['id']


@lru_cache()
def get_movie(id: str) -> MovieResponse:
    return MovieResponse(**get_json(f'movie/{id}'))


@ttl_cache()
def get_tv(id: str) -> TvApiResponse:
    return TvApiResponse(**get_json(f'tv/{id}'))


def get_movie_imdb_id(movie_id: Union[int, str]) -> str:
    return get_imdb_id('movie', movie_id)


def get_tv_imdb_id(tv_id: Union[int, str]) -> str:
    return get_imdb_id('tv', tv_id)


@lru_cache()
def get_imdb_id(type: str, id: Union[int, str]) -> str:
    return get_json(f'{type}/{id}/external_ids')['imdb_id']


@ttl_cache()
def get_tv_episodes(id: str, season: str) -> TvSeasonResponse:
    return TvSeasonResponse(**get_json(f'tv/{id}/season/{season}'))


class ReleaseType(Enum):
    PREMIERE = 1
    THEATRICAL_LIMITED = 2
    THEATRICAL = 3
    DIGITAL = 4
    PHYSICAL = 5
    TV = 6


def discover(types=(ReleaseType.PHYSICAL, ReleaseType.DIGITAL)):
    return get_json(
        'discover/movie',
        params={
            'sort_by': ','.join(('popularity.desc', 'primary_release_date.desc')),
            'primary_release_date.lte': date.today().isoformat(),
            'with_release_type': '|'.join(str(ReleaseType(i).value) for i in types),
        },
    )
