import logging
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


PROVIDERS = [
    HorriblesubsProvider(),
    RarbgProvider(),
    KickassProvider(),
    TorrentsCsvProvider(),
    NyaaProvider(),
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
