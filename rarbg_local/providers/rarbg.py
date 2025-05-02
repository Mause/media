import json
import logging
from json.decoder import JSONDecodeError
from typing import Dict, Iterator, List, TypedDict

import backoff
import requests

from .abc import MovieProvider, TvProvider

logger = logging.getLogger(__name__)

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
        'User-Agent': "rarbg api client - me+rarbg@mause.me",
        'X-Server-Contact': 'me+rarbg@mause.me',
    }
)


def get_token(base):
    return session.get(base, params={'get_token': 'get_token'}).json()['token']


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
NONE = {
    'No results found',
    'Cant find search_imdb in database',
    'Cant find imdb in database',
}


def load_category_codes() -> Dict[str, int]:
    with open('categories.json') as fh:
        return json.load(fh)


class RarbgTorrent(TypedDict):
    category: str
    seeders: int
    title: str
    download: str


def get_rarbg_iter(base_url: str, type: str, **kwargs) -> Iterator[List[RarbgTorrent]]:
    codes = load_category_codes()
    categories = [codes[key] for key in CATEGORIES[type]]

    return map(
        lambda category: _get(base_url, **dict(kwargs, category=str(category))),
        categories,
    )


class TooManyRequests(Exception):
    pass


@backoff.on_exception(backoff.expo, (TooManyRequests,))
def _get(base_url: str, **kwargs: str) -> List[Dict]:
    assert isinstance(session.params, dict)
    if 'token' not in session.params:
        session.params['token'] = get_token(base_url)

    r = session.get(base_url, params=kwargs)
    if r.status_code == 429:
        raise TooManyRequests()

    r.raise_for_status()

    try:
        res = r.json()
    except JSONDecodeError as e:
        raise Exception(r, r.reason, r.headers, r.request.url, r.text) from e

    error = res.get('error')
    if res.get('error_code') == 4:
        logger.info('Token expired, reacquiring')
        session.params['token'] = get_token(base_url)
        res = _get(**kwargs)
    elif error:
        if any(message in error for message in NONE):
            pass
        elif 'Too many requests' in error:
            raise TooManyRequests(res)
        else:
            raise Exception(res)

    return res.get('torrent_results', [])


class RarbgProvider(TvProvider, MovieProvider):
    name = 'rarbg'
    type = ProviderSource.RARBG

    async def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
    ) -> AsyncGenerator[ITorrent, None]:
        if not imdb_id:
            return

        search_string = format(season, episode)

        for item in chain.from_iterable(
            get_rarbg_iter(
                'https://torrentapi.org/pubapi_v2.php',
                'series',
                search_imdb=imdb_id,
                search_string=search_string,
            )
        ):
            yield ITorrent(
                source=ProviderSource.RARBG,
                title=item['title'],
                seeders=item['seeders'],
                download=item['download'],
                category=tv_convert(item['category']),
                episode_info=EpisodeInfo(seasonnum=str(season), epnum=str(episode)),
            )

    async def search_for_movie(
        self, imdb_id: str, tmdb_id: int
    ) -> AsyncGenerator[ITorrent, None]:
        for item in chain.from_iterable(
            get_rarbg_iter(
                'https://torrentapi.org/pubapi_v2.php', 'movie', search_imdb=imdb_id
            )
        ):
            yield ITorrent(
                source=ProviderSource.RARBG,
                title=item['title'],
                seeders=item['seeders'],
                download=item['download'],
                category=movie_convert(item['category']),
            )
