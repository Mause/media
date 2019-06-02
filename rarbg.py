# coding: utf-8

import json
import logging
from itertools import chain

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
session.headers['User-Agent'] = "Dom's api client    - me+rarbg@mause.me"


def get_token():
    return session.get(BASE, params={'get_token': 'get_token'}).json()['token']


TV_CATEGORIES = {"TV Episodes", "TV HD Episodes", "TV UHD Episodes"}
MOVIE_CATEGORIES = {
    "Movies/BD Remux",
    "Movies/Full BD",
    "Movies/XVID",
    "Movies/XVID/720",
    "Movies/x264",
    "Movies/x264/1080",
    "Movies/x264/3D",
    "Movies/x264/4k",
    "Movies/x264/720",
    "Movies/x265/4k",
    "Movs/x265/4k/HDR",
}


def get(type, **kwargs):
    from concurrent.futures import ThreadPoolExecutor

    if 'token' not in session.params:
        session.params['token'] = get_token()

    with open('categories.json') as fh:
        categories = json.load(fh)

    return chain.from_iterable(
        ThreadPoolExecutor(10).map(
            lambda category: _get(**kwargs, category=category), categories
        )
    )


def _get(**kwargs):
    r = session.get(
        BASE, params=kwargs, headers={'X-Server-Contact': 'me+rarbg@mause.me'}
    )
    print(r.request.url)
    from json.decoder import JSONDecodeError

    try:
        res = r.json()
    except JSONDecodeError as e:
        raise Exception(r, r.request.url, r.text) from e

    print(res.keys())

    if res.get('error_code') == 4:
        logging.info('Token expired, reacquiring')
        session.params['token'] = get_token()
        res = _get(**kwargs)
    elif 'error' in res and res['error'] != 'No results found':
        raise Exception(res)

    res = res.get('torrent_results', [])
    if res:
        print(res[-1].keys())
    return res
