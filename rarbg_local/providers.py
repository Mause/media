from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from itertools import chain
from queue import Empty, Queue
from threading import Semaphore, current_thread
from typing import Callable, Iterable, List, Optional, Tuple, TypeVar

from . import horriblesubs, kickass
from .models import EpisodeInfo, ITorrent, ProviderSource
from .rarbg import get_rarbg_iter
from .tmdb import get_tv

T = TypeVar('T')
ProviderType = Callable[..., Iterable[T]]


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


class Provider(ABC):
    name: str

    @abstractmethod
    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int = None
    ) -> Iterable[ITorrent]:
        raise NotImplementedError()

    @abstractmethod
    def search_for_movie(self, imdb_id: str, tmdb_id: int) -> Iterable[ITorrent]:
        raise NotImplementedError()


class RarbgProvider(Provider):
    name = 'rarbg'

    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int = None
    ) -> Iterable[ITorrent]:
        if not imdb_id:
            return []

        search_string = f'S{season:02d}E{episode:02d}' if episode else f'S{season:02d}'

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
                category=movie_convert(item['category']),
                episode_info=EpisodeInfo(None, None),
            )


class KickassProvider(Provider):
    name = 'kickass'

    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int = None
    ) -> Iterable[ITorrent]:
        if not imdb_id:
            return []

        for item in kickass.search_for_tv(imdb_id, tmdb_id, season, episode):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=tv_convert(item['resolution']),
                episode_info=EpisodeInfo(str(season), str(episode)),
            )

    def search_for_movie(self, imdb_id: str, tmdb_id: int) -> Iterable[ITorrent]:
        for item in kickass.search_for_movie(imdb_id, tmdb_id):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=movie_convert(item['resolution']),
                episode_info=EpisodeInfo(None, None),
            )


class HorriblesubsProvider(Provider):
    name = 'horriblesubs'

    def search_for_tv(
        self, imdb_id: Optional[str], tmdb_id: int, season: int, episode: int = None
    ) -> Iterable[ITorrent]:
        name = get_tv(tmdb_id)['name']
        template = f'HorribleSubs {name} S{season:02d}'

        for item in horriblesubs.search_for_tv(tmdb_id, season, episode):
            yield ITorrent(
                source=ProviderSource.HORRIBLESUBS,
                title=f'{template}E{int(item["episode"], 10):02d} {item["resolution"]}',
                seeders=0,
                download=item['download'],
                category=tv_convert(item['resolution']),
                episode_info=EpisodeInfo(str(season), str(item['episode'])),
            )

    def search_for_movie(self, imdb_id: str, tmdb_id: int) -> Iterable[ITorrent]:
        return []


PROVIDERS = [HorriblesubsProvider(), RarbgProvider(), KickassProvider()]


def threadable(functions: List[ProviderType], args: Tuple) -> Iterable[T]:
    def worker(function: ProviderType) -> None:
        try:
            current_thread().setName(function.__name__)

            for item in function(*args):
                queue.put(item)
        finally:
            s.release()

    s = Semaphore(0)
    queue: Queue[T] = Queue()
    executor = ThreadPoolExecutor(len(functions))

    futures = executor.map(worker, functions)

    while getattr(s, '_value') != len(functions) or not queue.empty():
        try:
            yield queue.get_nowait()
        except Empty:
            pass

    list(futures)  # throw exceptions in this thread


def search_for_tv(imdb_id: str, tmdb_id: int, season: int, episode: int = None):
    return threadable(
        [provider.search_for_tv for provider in PROVIDERS],
        (imdb_id, tmdb_id, season, episode),
    )


def search_for_movie(imdb_id: str, tmdb_id: int):
    return threadable(
        [provider.search_for_movie for provider in PROVIDERS], (imdb_id, tmdb_id)
    )


class FakeProvider(Provider):
    def search_for_tv(self, *args, **kwargs):
        return (search_for_tv(*args, **kwargs),)

    def search_for_movie(self, *args, **kwargs):
        return search_for_movie(*args, **kwargs)


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
