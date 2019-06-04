from typing import Dict, List
from itertools import chain
from functools import lru_cache

from requests_toolbelt.sessions import BaseUrlSession

tmdb = BaseUrlSession('https://api.themoviedb.org/3/')
tmdb.params['api_key'] = '66b197263af60702ba14852b4ec9b143'


def try_(dic: Dict[str, str], *keys: str) -> str:
    return next(dic[key] for key in keys if key in dic)


@lru_cache()
def search_themoviedb(s: str) -> List[Dict]:
    MAP = {'tv': 'series', 'movie': 'movie'}
    r = tmdb.get('search/multi', params={'query': s})
    return [
        {
            'Type': MAP[result['media_type']],
            'title': try_(result, 'title', 'name'),
            'Year': try_(result, 'first_air_date', 'release_date').split('-')[
                0
            ],
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

    return next(item for item in chain.from_iterable(results.values()))['id']


@lru_cache()
def get_movie(id: str):
    return tmdb.get(f'movie/{id}').json()


@lru_cache()
def get_tv(id: str):
    return tmdb.get(f'tv/{id}').json()


def get_movie_imdb_id(tv_id: str) -> str:
    return get_imdb_id('movie', tv_id)


def get_tv_imdb_id(tv_id: str) -> str:
    return get_imdb_id('tv', tv_id)


@lru_cache()
def get_imdb_id(type: str, id: str) -> str:
    return tmdb.get(f'{type}/{id}/external_ids').json()['imdb_id']


@lru_cache()
def get_tv_episodes(id: str, season: str):
    return tmdb.get(f'tv/{id}/season/{season}').json()


def cache_clear():
    for key, value in globals().items():
        print(key)
        if hasattr(value, 'cache_clear'):
            print(value)
            value.cache_clear()
