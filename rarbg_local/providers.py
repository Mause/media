from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from itertools import chain
from queue import Empty, Queue
from threading import Semaphore, current_thread
from typing import AsyncGenerator, Callable, Iterable, List, Optional, Tuple, TypeVar

import aiohttp

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
        self, imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
    ) -> AsyncGenerator[ITorrent, None]:
        raise NotImplementedError()

    @abstractmethod
    def search_for_movie(
        self, imdb_id: str, tmdb_id: int
    ) -> AsyncGenerator[ITorrent, None]:
        raise NotImplementedError()


class RarbgProvider(Provider):
    name = 'rarbg'

    async def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
    ) -> AsyncGenerator[ITorrent, None]:
        if not imdb_id:
            return

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
                episode_info=EpisodeInfo(),
            )


class KickassProvider(Provider):
    name = 'kickass'

    async def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
    ) -> AsyncGenerator[ITorrent, None]:
        if not imdb_id:
            return

        for item in await kickass.search_for_tv(imdb_id, tmdb_id, season, episode):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=tv_convert(item['resolution']),
                episode_info=EpisodeInfo(
                    seasonnum=str(season),
                    epnum=None if episode is None else str(episode),
                ),
            )

    async def search_for_movie(
        self, imdb_id: str, tmdb_id: int
    ) -> AsyncGenerator[ITorrent, None]:
        for item in await kickass.search_for_movie(imdb_id, tmdb_id):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=movie_convert(item['resolution']),
                episode_info=EpisodeInfo(),
            )


class HorriblesubsProvider(Provider):
    name = 'horriblesubs'

    async def search_for_tv(
        self,
        imdb_id: Optional[str],
        tmdb_id: int,
        season: int,
        episode: Optional[int] = None,
    ) -> AsyncGenerator[ITorrent, None]:
        name = (await get_tv(tmdb_id)).name
        template = f'HorribleSubs {name} S{season:02d}'

        for item in await horriblesubs.search_for_tv(tmdb_id, season, episode):
            yield ITorrent(
                source=ProviderSource.HORRIBLESUBS,
                title=f'{template}E{int(item["episode"], 10):02d} {item["resolution"]}',
                seeders=0,
                download=item['download'],
                category=tv_convert(item['resolution']),
                episode_info=EpisodeInfo(
                    seasonnum=str(season), epnum=str(item['episode'])
                ),
            )

    async def search_for_movie(
        self, imdb_id: str, tmdb_id: int
    ) -> AsyncGenerator[ITorrent, None]:
        if not True:
            yield


class TorrentsCsvProvider(Provider):
    def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: int = None
    ) -> AsyncGenerator[ITorrent, None]:
        pass

    name = "torrentscsv"

    async def search_for_movie(
        self, imdb_id: str, tmdb_id: int
    ) -> AsyncGenerator[ITorrent, None]:
        async with aiohttp.ClientSession() as session:
            res = await session.get(
                "https://torrents-csv.com/service/search", params={"q": imdb_id}
            )
            for item in (await res.json())['torrents']:
                yield ITorrent(
                    source=ProviderSource.TORRENTS_CSV,
                    title=item['name'],
                    seeders=item['seeders'],
                    download=item['infohash'],
                    episode_info=EpisodeInfo(),
                )


PROVIDERS = [
    HorriblesubsProvider(),
    RarbgProvider(),
    KickassProvider(),
    TorrentsCsvProvider(),
]


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


async def search_for_tv(
    imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
):
    for provider in PROVIDERS:
        async for result in provider.search_for_tv(imdb_id, tmdb_id, season, episode):
            yield result


async def search_for_movie(imdb_id: str, tmdb_id: int):
    for provider in PROVIDERS:
        async for result in provider.search_for_movie(imdb_id, tmdb_id):
            yield result


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
