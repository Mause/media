from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

from ..models import ITorrent, ProviderSource


class Provider(ABC):
    name: str
    type: ProviderSource


class TvProvider(Provider):
    @abstractmethod
    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
    ) -> AsyncGenerator[ITorrent, None]:
        raise NotImplementedError()


class MovieProvider(Provider):
    @abstractmethod
    def search_for_movie(
        self, imdb_id: str, tmdb_id: int
    ) -> AsyncGenerator[ITorrent, None]:
        raise NotImplementedError()


def tv_convert(key):
    return {
        '480': 'TV Episodes',
        '480p': 'TV Episodes',
        '720': 'TV Episodes',
        '720p': 'TV Episodes',
        '1080': 'TV HD Episodes',
        '1080p': 'TV HD Episodes',
        'x264': 'TV HD Episodes',
    }.get(key, key)


def movie_convert(key):
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


def format(season: int, episode: Optional[int]) -> str:
    return f'S{season:02d}E{episode:02d}' if episode else f'S{season:02d}'
