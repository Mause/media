from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable

from . import horriblesubs, kickass
from .models import EpisodeInfo, ITorrent, ProviderSource
from .rarbg import get_rarbg_iter
from .tmdb import get_tv


class Provider(ABC):
    @abstractmethod
    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int
    ) -> Iterable[ITorrent]:
        raise NotImplementedError()

    @abstractmethod
    def search_for_movie(self, imdb_id: str, tmdb_id: int) -> Iterable[ITorrent]:
        raise NotImplementedError()


class RarbgProvider(Provider):
    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int
    ) -> Iterable[ITorrent]:
        if not imdb_id:
            return []

        for item in chain.from_iterable(
            get_rarbg_iter(
                'https://torrentapi.org/pubapi_v2.php',
                'series',
                search_imdb=imdb_id,
                search_string=f'S{season:02d}E{episode:02d}',
            )
        ):
            yield ITorrent(
                source=ProviderSource.RARBG,
                title=item['title'],
                seeders=item['seeders'],
                download=item['download'],
                category=item['category'],
                episode_info=EpisodeInfo(str(season), str(episode)),
            )

    def search_for_movie(self, imdb_id: str, tmdb_id: int) -> Iterable[ITorrent]:
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
                category=item['category'],
                episode_info=EpisodeInfo(None, None),
            )


class KickassProvider(Provider):
    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int
    ) -> Iterable[ITorrent]:
        if not imdb_id:
            return []

        for item in kickass.search_for_tv(imdb_id, tmdb_id, season, episode):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=item['resolution'],
                episode_info=EpisodeInfo(str(season), str(episode)),
            )

    def search_for_movie(self, imdb_id: str, tmdb_id: int) -> Iterable[ITorrent]:
        for item in kickass.search_for_movie(imdb_id, tmdb_id):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=item['resolution'],
                episode_info=EpisodeInfo(None, None),
            )


class HorriblesubsProvider(Provider):
    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int
    ) -> Iterable[ITorrent]:
        name = get_tv(tmdb_id)['name']
        for item in horriblesubs.search_for_tv(tmdb_id, season, episode):
            yield ITorrent(
                source=ProviderSource.HORRIBLESUBS,
                title=f'{name} {item["resolution"]} S{season:02d}E{episode:02d}',
                seeders=0,
                download=item['download'],
                category=item['resolution'],
                episode_info=EpisodeInfo(str(season), str(episode)),
            )

    def search_for_movie(self, imdb_id: str, tmdb_id: int) -> Iterable[ITorrent]:
        return []


PROVIDERS = [HorriblesubsProvider(), RarbgProvider(), KickassProvider()]


def search_for_tv(imdb_id: str, tmdb_id: int, season: int, episode: int):
    return chain.from_iterable(
        provider.search_for_tv(imdb_id, tmdb_id, season, episode)
        for provider in PROVIDERS
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
