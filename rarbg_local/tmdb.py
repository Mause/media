from datetime import date
from enum import Enum
from itertools import chain
from typing import Dict, List, Optional

import backoff
import requests
from requests_toolbelt.sessions import BaseUrlSession

from .utils import lru_cache

tmdb = BaseUrlSession('https://api.themoviedb.org/3/')
tmdb.params['api_key'] = '66b197263af60702ba14852b4ec9b143'


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


@lru_cache()
def search_themoviedb(s: str) -> List[Dict]:
    MAP = {'tv': 'series', 'movie': 'movie'}
    r = tmdb.get('search/multi', params={'query': s})
    return [
        {
            'Type': MAP[result['media_type']],
            'title': try_(result, 'title', 'name'),
            'Year': get_year(result),
            'imdbID': result['id'],
        }
        for result in r.json()['results']
        if result['media_type'] in MAP
    ]


@lru_cache()
def find_themoviedb(i: str):
    assert i.startswith('tt')
    results = tmdb.get(
        f'find/{i}', params={'external_source': 'imdb_id'}
    ).json()

    result = next(item for item in chain.from_iterable(results.values()))

    return dict(result, title=result['original_name'])


@lru_cache()
def resolve_id(imdb_id: str) -> str:
    assert imdb_id.startswith('tt')
    results = tmdb.get(
        f'find/{imdb_id}', params={'external_source': 'imdb_id'}
    ).json()

    res = next((item for item in chain.from_iterable(results.values())), None)
    assert res, f'No results for {imdb_id}'
    return res['id']


@lru_cache()
def get_movie(id: str):
    return get_json(f'movie/{id}')


@lru_cache()
def get_tv(id: str):
    return get_json(f'tv/{id}')


def get_movie_imdb_id(tv_id: str) -> str:
    return get_imdb_id('movie', tv_id)


def get_tv_imdb_id(tv_id: str) -> str:
    return get_imdb_id('tv', tv_id)


@lru_cache()
def get_imdb_id(type: str, id: str) -> str:
    return get_json(f'{type}/{id}/external_ids')['imdb_id']


@lru_cache()
def get_tv_episodes(id: str, season: str):
    return get_json(f'tv/{id}/season/{season}')


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
