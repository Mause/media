import json
import logging
from collections.abc import AsyncGenerator, Iterator
from itertools import chain
from json.decoder import JSONDecodeError
from typing import Any

import backoff
import requests
from healthcheck import HealthcheckCallbackResponse
from pydantic import BaseModel

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..types import ImdbId, TmdbId
from ..utils import format_marker
from .abc import MovieProvider, TvProvider, movie_convert, tv_convert

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


def get_token(base: str) -> str:
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


def load_category_codes() -> dict[str, int]:
    with open('categories.json') as fh:
        return json.load(fh)


class RarbgTorrent(BaseModel):
    category: str
    seeders: int
    title: str
    download: str


class RarbgResponse(BaseModel):
    error: str | None = None
    error_code: int | None = None
    torrent_results: list[RarbgTorrent] = []


def get_rarbg_iter(
    base_url: str, type: str, **kwargs: Any
) -> Iterator[list[RarbgTorrent]]:
    codes = load_category_codes()
    categories = [codes[key] for key in CATEGORIES[type]]

    return map(
        lambda category: _get(base_url, category=str(category), **kwargs),
        categories,
    )


class TooManyRequests(Exception):
    pass


@backoff.on_exception(backoff.expo, (TooManyRequests,))
def _get(base_url: str, **kwargs: str) -> list[RarbgTorrent]:
    assert isinstance(session.params, dict)
    if 'token' not in session.params:
        session.params['token'] = get_token(base_url)

    r = session.get(base_url, params=kwargs)
    if r.status_code == 429:
        raise TooManyRequests()

    r.raise_for_status()

    try:
        res = RarbgResponse.model_validate(r.json())
    except JSONDecodeError as e:
        raise Exception(r, r.reason, r.headers, r.request.url, r.text) from e

    error = res.error
    if res.error_code == 4:
        logger.info('Token expired, reacquiring')
        session.params['token'] = get_token(base_url)
        return _get(**kwargs)
    elif error:
        if any(message in error for message in NONE):
            pass
        elif 'Too many requests' in error:
            raise TooManyRequests(res)
        else:
            raise Exception(res)

    return res.torrent_results


class RarbgProvider(TvProvider, MovieProvider):
    type = ProviderSource.RARBG
    root = 'https://torrentapi.org'

    async def search_for_tv(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
        season: int,
        episode: int | None = None,
    ) -> AsyncGenerator[ITorrent, None]:
        if not imdb_id:
            return

        search_string = format_marker(season, episode)

        for item in chain.from_iterable(
            get_rarbg_iter(
                self.root + '/pubapi_v2.php',
                'series',
                search_imdb=imdb_id,
                search_string=search_string,
            )
        ):
            yield ITorrent(
                source=ProviderSource.RARBG,
                title=item.title,
                seeders=item.seeders,
                download=item.download,
                category=tv_convert(item.category),
                episode_info=EpisodeInfo(seasonnum=season, epnum=episode),
            )

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        for item in chain.from_iterable(
            get_rarbg_iter(self.root + '/pubapi_v2.php', 'movie', search_imdb=imdb_id)
        ):
            yield ITorrent(
                source=ProviderSource.RARBG,
                title=item.title,
                seeders=item.seeders,
                download=item.download,
                category=movie_convert(item.category),
            )

    async def health(self) -> HealthcheckCallbackResponse:
        return await self.check_http(self.root)
