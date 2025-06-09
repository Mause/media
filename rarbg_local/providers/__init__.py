import logging
from asyncio import Future, Queue
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
    # from .horriblesubs import HorriblesubsProvider
    # from .kickass import KickassProvider
    from .nyaasi import NyaaProvider
    from .piratebay import PirateBayProvider

    # from .rarbg import RarbgProvider
    from .torrents_csv import TorrentsCsvProvider

    return [
        # HorriblesubsProvider(),
        # RarbgProvider(),
        # KickassProvider(),
        TorrentsCsvProvider(),
        NyaaProvider(),
        PirateBayProvider(),
    ]


async def search_for_tv(
    imdb_id: ImdbId, tmdb_id: TmdbId, season: int, episode: int | None = None
) -> tuple[list[Future[None]], Queue[ITorrent | Message]]:
    async def worker(
        output_queue: Queue[ITorrent | Message], provider: TvProvider
    ) -> None:
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
) -> tuple[list[Future[None]], Queue[ITorrent | Message]]:
    async def worker(
        output_queue: Queue[ITorrent | Message], provider: MovieProvider
    ) -> None:
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
    worker: Callable[[Queue[ITorrent | Message], TT], Coroutine[Any, Any, None]],
    providers: list[TT],
) -> tuple[list[Future[None]], Queue[ITorrent | Message]]:
    output_queue = Queue[ITorrent | Message]()
    tasks = [
        create_monitored_task(worker(output_queue, provider), output_queue.put_nowait)
        for provider in providers
    ]
    return tasks, output_queue
