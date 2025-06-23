from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

import aiohttp
from healthcheck import HealthcheckCallbackResponse, HealthcheckStatus

from ..models import ITorrent, ProviderSource
from ..types import ImdbId, TmdbId


async def check_http(url: str, method: str = 'HEAD') -> HealthcheckCallbackResponse:
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url) as response:
            if response.status == 200:
                return HealthcheckCallbackResponse(
                    HealthcheckStatus.PASS, repr(response)
                )
            else:
                return HealthcheckCallbackResponse(
                    HealthcheckStatus.FAIL, f'Failed to reach {url}: {response.status}'
                )


class Provider(ABC):
    type: ProviderSource

    @abstractmethod
    async def health(self) -> HealthcheckCallbackResponse:
        raise NotImplementedError()

    async def check_http(
        self, url: str, method: str = 'HEAD'
    ) -> HealthcheckCallbackResponse:
        return await check_http(url, method)


class TvProvider(Provider):
    @abstractmethod
    def search_for_tv(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
        season: int,
        episode: int | None = None,
    ) -> AsyncGenerator[ITorrent, None]:
        raise NotImplementedError()


class MovieProvider(Provider):
    @abstractmethod
    def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        raise NotImplementedError()


def tv_convert(key: str) -> str:
    return {
        '480': 'TV Episodes',
        '480p': 'TV Episodes',
        '720': 'TV Episodes',
        '720p': 'TV Episodes',
        '1080': 'TV HD Episodes',
        '1080p': 'TV HD Episodes',
        'x264': 'TV HD Episodes',
    }.get(key, key)


def movie_convert(key: str) -> str:
    return {
        # None: "XVID",
        # None: "x264",
        '720': "x264/720",
        '720p': "x264/720",
        # None: "XVID/720",
        # None: "BD Remux",
        # None: "Full BD",
        '1080p': "x264/1080",
        '1080': "x264/1080",
        # None: "x264/4k",
        # None: "x265/4k",
        # None: "x264/3D",
        # None: "x265/4k/HDR",
    }.get(key, key)
