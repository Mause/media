from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable

from . import horriblesubs, kickass
from .models import EpisodeInfo, ITorrent
from .rarbg import get_rarbg_iter


class Provider(ABC):
    @abstractmethod
    def search_for_tv(
        self, imdb_id: str, season: int, episode: int
    ) -> Iterable[ITorrent]:
        raise NotImplementedError()

    @abstractmethod
    def search_for_movie(self, imdb_id: str, tmdb_id: int) -> Iterable[ITorrent]:
        raise NotImplementedError()


class RarbgProvider(Provider):
    def search_for_tv(self, imdb_id, season, episode) -> Iterable[ITorrent]:
        for item in chain.from_iterable(
            get_rarbg_iter(
                'https://torrentapi.org/pubapi_v2.php',
                'series',
                search_imdb=imdb_id,
                search_string=f'S{season:02d}E{episode:02d}',
            )
        ):
            yield ITorrent(
                source='Rarbg',
                title=item['title'],
                seeders=item['seeders'],
                download=item['download'],
                category=item['category'],
                episode_info=EpisodeInfo(season, episode),
            )

    def search_for_movie(self, imdb_id, tmdb_id) -> Iterable[ITorrent]:
        for item in chain.from_iterable(
            get_rarbg_iter(
                'https://torrentapi.org/pubapi_v2.php', 'movie', search_imdb=imdb_id
            )
        ):
            yield ITorrent(
                source='Rarbg',
                title=item['title'],
                seeders=item['seeders'],
                download=item['download'],
                category=item['category'],
                episode_info=EpisodeInfo(None, None),
            )


class KickassProvider(Provider):
    def search_for_tv(self, imdb_id, season, episode) -> Iterable[ITorrent]:
        for item in kickass.search_for_tv(imdb_id, season, episode):
            yield ITorrent(
                source='Kickass',
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=item['resolution'],
                episode_info=EpisodeInfo(season, episode),
            )

    def search_for_movie(self, imdb_id, tmdb_id):
        for item in kickass.search_for_movie(tmdb_id):
            yield ITorrent(
                source='Kickass',
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=item['resolution'],
                episode_info=EpisodeInfo(None, None),
            )


class HorriblesubsProvider(Provider):
    def search_for_tv(self, imdb_id, season, episode) -> Iterable[ITorrent]:
        for item in horriblesubs.search_for_tv(imdb_id, season, episode):
            yield ITorrent(
                source='HorribleSubs',
                title='',
                seeders=0,
                download=item,
                category='1080p',
                episode_info=EpisodeInfo(season, episode),
            )

    def search_for_movie(self, imdb_id, tmdb_id):
        return []


PROVIDERS = [HorriblesubsProvider(), RarbgProvider(), KickassProvider()]


def search_for_tv(imdb_id: str, season, episode):
    return chain.from_iterable(
        provider.search_for_tv(imdb_id, season, episode) for provider in PROVIDERS
    )


def search_for_movie(imdb_id: str, tmdb_id: int):
    return chain.from_iterable(
        provider.search_for_movie(imdb_id, tmdb_id) for provider in PROVIDERS
    )


def main():
    from tabulate import tabulate

    print(
        tabulate(
            list(
                [row.source, row.title, row.seeders, bool(row.download)]
                for row in search_for_tv('tt0436992', 1, 1)
            ),
            headers=('Source', 'Title', 'Seeders', 'Has magnet'),
        )
    )


if __name__ == '__main__':
    main()
