# coding: utf-8

import json
import logging
from itertools import chain
from typing import List, Dict

import backoff
import requests


BASE = 'https://torrentapi.org/pubapi_v2.php'
session = requests.Session()
session.params = {
    'mode': 'search',
    'ranked': '0',
    'limit': '100',
    'format': 'json_extended',
    'app_id': 'Sonarr',
}
session.headers.update(
    {
        'User-Agent': "Dom's api client - me+rarbg@mause.me",
        'X-Server-Contact': 'me+rarbg@mause.me',
    }
)


def get_token():
    return session.get(BASE, params={'get_token': 'get_token'}).json()['token']


CATEGORIES = {
    'movie': {
        "Movies/BD Remux",
        "Movies/Full BD",
        "Movies/XVID",
        "Movies/x264",
        "Movies/x264/720",
        "Movies/XVID/720",
        "Movies/x264/3D",
        "Movies/x264/1080",
        "Movies/x264/4k",
        "Movies/x265/4k",
        "Movs/x265/4k/HDR",
    },
    'series': {"TV Episodes", "TV HD Episodes", "TV UHD Episodes"},
}


def load_category_codes() -> Dict[str, int]:
    with open('categories.json') as fh:
        return json.load(fh)


def get_rarbg(type, **kwargs):
    return list(get_rarbg_iter(type, **kwargs))


def get_rarbg_iter(type, **kwargs):
    if 'token' not in session.params:
        session.params['token'] = get_token()

    codes = load_category_codes()
    categories = [codes[key] for key in CATEGORIES[type]]

    return chain.from_iterable(
        map(
            lambda category: _get(**kwargs, category=category), categories
        )
    )


class TooManyRequests(Exception):
    pass


@backoff.on_exception(backoff.expo, (TooManyRequests,))
def _get(**kwargs: str) -> List[Dict]:
    r = session.get(BASE, params=kwargs)
    if r.status_code == 429:
        raise TooManyRequests()

    r.raise_for_status()
    print(r.request.url)
    from json.decoder import JSONDecodeError

    try:
        res = r.json()
    except JSONDecodeError as e:
        raise Exception(r, r.reason, r.headers, r.request.url, r.text) from e

    print(res.keys())

    error = res.get('error')

    if res.get('error_code') == 4:
        logging.info('Token expired, reacquiring')
        assert isinstance(session.params, dict)
        session.params['token'] = get_token()
        res = _get(**kwargs)
    elif error:
        if error == 'No results found':
            pass
        elif 'Too many requests' in error:
            raise TooManyRequests(res)
        else:
            raise Exception(res)

    return res.get('torrent_results', [])
