import logging
from asyncio import Future, Queue
from collections.abc import Callable, Coroutine, Iterable
from typing import TYPE_CHECKING, Any

from ..models import ITorrent
from ..types import ImdbId, TmdbId
from ..utils import Message, create_monitored_task
from .abc import MovieProvider, Provider, TvProvider
from .auth import User, get_current_user
from .health import get
from .statsig_service import get_statsig

if TYPE_CHECKING:
    from statsig_python_core import Statsig

type ProviderType[T] = Callable[..., Iterable[T]]
logger = logging.getLogger(__name__)


async def get_providers() -> list[Provider]:
    from statsig_python_core import StatsigUser

    # from .horriblesubs import HorriblesubsProvider
    # from .kickass import KickassProvider
    from .luna import LunaProvider
    from .nyaasi import NyaaProvider
    from .piratebay import PirateBayProvider

    # from .rarbg import RarbgProvider
    from .torrents_csv import TorrentsCsvProvider

    providers: list[Provider] = [
        # HorriblesubsProvider(),
        # RarbgProvider(),
        # KickassProvider(),
        TorrentsCsvProvider(),
        NyaaProvider(),
        PirateBayProvider(),
    ]

    statsig: 'Statsig' = await get(get_statsig)
    user: User = await get(get_current_user)

    if statsig.check_gate(StatsigUser(user.name), 'luna'):
        providers.append(LunaProvider())

    return providers


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
        [provider for provider in await get_providers() if isinstance(provider, TvProvider)],
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
            for provider in await get_providers()
            if isinstance(provider, MovieProvider)
        ],
    )


async def spin_up_workers[TT: Provider](
    worker: Callable[[Queue[ITorrent | Message], TT], Coroutine[Any, Any, None]],
    providers: list[TT],
) -> tuple[list[Future[None]], Queue[ITorrent | Message]]:
    output_queue = Queue[ITorrent | Message]()
    tasks = [
        create_monitored_task(worker(output_queue, provider), output_queue.put_nowait)
        for provider in providers
    ]
    return tasks, output_queue
