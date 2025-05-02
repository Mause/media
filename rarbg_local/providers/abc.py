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
