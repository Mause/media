import asyncio
import logging
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
from threading import Semaphore, current_thread
from typing import TypeVar

from ..models import ITorrent
from ..types import ImdbId, TmdbId
from ..utils import create_monitored_task
from .abc import MovieProvider, Provider

T = TypeVar('T')
ProviderType = Callable[..., Iterable[T]]
logger = logging.getLogger(__name__)


def get_providers() -> list[Provider]:
    from .horriblesubs import HorriblesubsProvider
    from .kickass import KickassProvider
    from .nyaasi import NyaaProvider
    from .piratebay import PirateBayProvider
    from .rarbg import RarbgProvider
    from .torrents_csv import TorrentsCsvProvider

    return [
        HorriblesubsProvider(),
        RarbgProvider(),
        KickassProvider(),
        TorrentsCsvProvider(),
        NyaaProvider(),
        PirateBayProvider(),
    ]


def threadable(functions: list[ProviderType], args: tuple) -> Iterable[T]:
    def worker(function: ProviderType) -> None:
        try:
            current_thread().name = function.__name__

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
    imdb_id: ImdbId, tmdb_id: TmdbId, season: int, episode: int | None = None
):
    from .abc import TvProvider

    for provider in get_providers():
        if not isinstance(provider, TvProvider):
            continue
        try:
            async for result in provider.search_for_tv(
                imdb_id, tmdb_id, season, episode
            ):
                yield result
        except Exception:
            logger.exception('Unable to load [TV] from %s', provider)


async def search_for_movie(
    imdb_id: ImdbId, tmdb_id: TmdbId
) -> tuple[list[asyncio.Future[None]], asyncio.Queue[ITorrent]]:
    async def worker(provider: MovieProvider):
        try:
            async for result in provider.search_for_movie(imdb_id, tmdb_id):
                output_queue.put_nowait(result)
        except Exception:
            logger.exception('Unable to load [MOVIE] from %s', provider)

    tasks = []
    output_queue = asyncio.Queue[ITorrent]()
    for provider in get_providers():
        if not isinstance(provider, MovieProvider):
            continue

        tasks.append(create_monitored_task(worker(provider), output_queue.put_nowait))
    return tasks, output_queue


async def main():
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.table import Table

    from ..tmdb import resolve_id

    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])

    table = Table(
        'Source',
        'Title',
        'Seeders',
        'Has magnet',
        show_header=True,
        header_style="bold magenta",
    )

    imdb_id = ImdbId('tt28454008')
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
