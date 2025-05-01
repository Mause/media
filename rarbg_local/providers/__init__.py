import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from itertools import chain
from queue import Empty, Queue
from threading import Semaphore, current_thread
from typing import AsyncGenerator, Callable, Iterable, List, Optional, Tuple, TypeVar

import aiohttp
from fastapi.concurrency import run_in_threadpool
from NyaaPy import nyaa

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..tmdb import get_tv
from . import horriblesubs, kickass
from .rarbg import get_rarbg_iter

T = TypeVar('T')
ProviderType = Callable[..., Iterable[T]]
logger = logging.getLogger(__name__)


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


def format(season: int, episode: Optional[int]) -> str:
    return f'S{season:02d}E{episode:02d}' if episode else f'S{season:02d}'


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


class KickassProvider(TvProvider, MovieProvider):
    name = 'kickass'
    type = ProviderSource.KICKASS

    async def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
    ) -> AsyncGenerator[ITorrent, None]:
        if not imdb_id:
            return

        async for item in kickass.search_for_tv(imdb_id, tmdb_id, season, episode):
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
        async for item in kickass.search_for_movie(imdb_id, tmdb_id):
            yield ITorrent(
                source=ProviderSource.KICKASS,
                title=item['title'],
                seeders=item['seeders'],
                download=item['magnet'],
                category=movie_convert(item['resolution']),
            )


class HorriblesubsProvider(TvProvider):
    name = 'horriblesubs'
    type = ProviderSource.HORRIBLESUBS

    async def search_for_tv(
        self,
        imdb_id: Optional[str],
        tmdb_id: int,
        season: int,
        episode: Optional[int] = None,
    ) -> AsyncGenerator[ITorrent, None]:
        name = (await get_tv(tmdb_id)).name
        template = f'HorribleSubs {name} S{season:02d}'

        async for item in horriblesubs.search_for_tv(tmdb_id, season, episode):
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


class TorrentsCsvProvider(MovieProvider):
    name = "torrentscsv"
    type = ProviderSource.TORRENTS_CSV

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
                )


class NyaaProvider(TvProvider):
    name = 'nyaa'
    type = ProviderSource.NYAA_SI

    async def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
    ) -> AsyncGenerator[ITorrent, None]:
        ny = nyaa.Nyaa()

        name = (await get_tv(tmdb_id)).name
        page = 0
        template = f'{name} ' + format(season, episode)

        def search():
            return ny.search(keyword=template, page=page)

        while True:
            items = await run_in_threadpool(search)
            if items:
                page += 1
            else:
                break

            for item in items:
                yield ITorrent(
                    source=ProviderSource.NYAA_SI,
                    title=item.name,
                    seeders=item.seeders,
                    download=item.magnet,
                    category=tv_convert(item.category),
                    episode_info=EpisodeInfo(season=season, episode=episode),
                )


class PirateBayProvider(TvProvider, MovieProvider):
    name = 'piratebay'
    root = 'https://apibay.org'

    async def search_for_tv(
        self, imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
    ) -> AsyncGenerator[ITorrent, None]:
        async with (
            aiohttp.ClientSession() as session,
            await session.get(
                self.root + '/q.php',
                params={'q': imdb_id + ' ' + format(season, episode)},
            ) as resp,
        ):
            data = await resp.json()

            if len(data) == 1 and data[0]['name'] == 'No results returned':
                return

            for item in data:
                yield ITorrent(
                    id=item['id'],
                    source=ProviderSource.PIRATEBAY,
                    title=item['name'],
                    seeders=item['seeders'],
                    download=item['info_hash'],
                    category=tv_convert(item['category']),
                    episode_info=EpisodeInfo(seasonnum=str(season), epnum=str(episode)),
                )

    async def search_for_movie(
        self, imdb_id: str, tmdb_id: int
    ) -> AsyncGenerator[ITorrent, None]:
        async with (
            aiohttp.ClientSession() as session,
            await session.get(self.root + '/q.php', params={'q': imdb_id}) as resp,
        ):
            data = await resp.json()

            if len(data) == 1 and data[0]['name'] == 'No results returned':
                return

            for item in data:
                yield ITorrent(
                    id=item['id'],
                    source=ProviderSource.PIRATEBAY,
                    title=item['name'],
                    seeders=item['seeders'],
                    download=item['info_hash'],
                    category=movie_convert(item['category']),
                )


PROVIDERS = [
    HorriblesubsProvider(),
    RarbgProvider(),
    KickassProvider(),
    TorrentsCsvProvider(),
    NyaaProvider(),
    PirateBayProvider(),
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
        if not isinstance(provider, TvProvider):
            continue
        try:
            async for result in provider.search_for_tv(
                imdb_id, tmdb_id, season, episode
            ):
                yield result
        except Exception:
            logger.exception('Unable to load [TV] from %s', provider.name)


async def search_for_movie(imdb_id: str, tmdb_id: int):
    for provider in PROVIDERS:
        if not isinstance(provider, MovieProvider):
            continue
        try:
            async for result in provider.search_for_movie(imdb_id, tmdb_id):
                yield result
        except Exception:
            logger.exception('Unable to load [MOVIE] from %s', provider.name)


async def main():
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.table import Table

    from .tmdb import resolve_id

    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])

    table = Table(
        'Source',
        'Title',
        'Seeders',
        'Has magnet',
        show_header=True,
        header_style="bold magenta",
    )

    imdb_id = 'tt28454008'
    tmdb_id = await resolve_id(imdb_id, 'tv')
    async for row in search_for_tv(
        imdb_id=imdb_id, tmdb_id=tmdb_id, season=1, episode=1
    ):
        table.add_row(
            row.source.name, row.title, str(row.seeders), str(bool(row.download))
        )

    Console().print(table)


if __name__ == '__main__':
    import uvloop

    uvloop.run(main())
