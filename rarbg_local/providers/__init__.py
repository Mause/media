import asyncio
import logging
from collections.abc import Callable, Coroutine, Iterable
from typing import Any, TypeVar

from ..models import ITorrent
from ..types import ImdbId, TmdbId
from ..utils import Message, create_monitored_task
from .abc import MovieProvider, Provider, TvProvider

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


async def search_for_tv(
    imdb_id: ImdbId, tmdb_id: TmdbId, season: int, episode: int | None = None
) -> tuple[list[asyncio.Future[None]], asyncio.Queue[ITorrent]]:
    async def worker(output_queue: asyncio.Queue[ITorrent], provider: TvProvider):
        try:
            async for result in provider.search_for_tv(
                imdb_id, tmdb_id, season, episode
            ):
                output_queue.put_nowait(result)
        except Exception:
            logger.exception('Unable to load [TV] from %s', provider)

    return await spin_up_workers(
        worker,
        [provider for provider in get_providers() if isinstance(provider, TvProvider)],
    )


async def search_for_movie(
    imdb_id: ImdbId, tmdb_id: TmdbId
) -> tuple[list[asyncio.Future[None]], asyncio.Queue[ITorrent]]:
    async def worker(output_queue: asyncio.Queue[ITorrent], provider: MovieProvider):
        try:
            async for result in provider.search_for_movie(imdb_id, tmdb_id):
                output_queue.put_nowait(result)
        except Exception:
            logger.exception('Unable to load [MOVIE] from %s', provider)

    return await spin_up_workers(
        worker,
        [
            provider
            for provider in get_providers()
            if isinstance(provider, MovieProvider)
        ],
    )


TT = TypeVar('TT', bound=Provider)


async def spin_up_workers(
    worker: Callable[[asyncio.Queue[ITorrent], TT], Coroutine[Any, Any, None]],
    providers: list[TT],
):
    output_queue = asyncio.Queue[ITorrent]()
    tasks = [
        create_monitored_task(worker(output_queue, provider), output_queue.put_nowait)
        for provider in providers
    ]
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
    tasks, queue = await search_for_tv(
        imdb_id=imdb_id, tmdb_id=tmdb_id, season=1, episode=1
    )

    while not all(task.done() for task in tasks):
        row = await queue.get()
        if isinstance(row, Message):
            print(row)
            continue
        table.add_row(
            row.source.name, row.title, str(row.seeders), str(bool(row.download))
        )

    Console().print(table)


if __name__ == '__main__':
    import uvloop

    uvloop.run(main())
