"""
<Guid id="imdb://tt28476983"/>
<Guid id="tmdb://6065761"/>
<Guid id="tvdb://10368107"/>

guid="plex://episode/65f11b8a1ddca1a96e3a9b72"
parentGuid="plex://season/64bbe921d10f4a2f439cdce6"
grandparentGuid="plex://show/64bab869275860ea7c00cc88"

guid="com.plexapp.agents.thetvdb://70327/1/1?lang=en"
parentGuid="com.plexapp.agents.thetvdb://70327/1?lang=en"
grandparentGuid="com.plexapp.agents.thetvdb://70327?lang=en"
"""

import logging
import os
from asyncio import gather, wait_for
from collections.abc import Callable, Sequence
from typing import Annotated
from urllib.parse import urlencode

from fastapi import Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from plexapi.myplex import X_PLEX_ENABLE_FAST_CONNECT, MyPlexAccount
from plexapi.server import PlexServer
from plexapi.video import Video
from sentry_sdk import trace
from yarl import URL

from .local_appender import local_appender
from .settings import Settings, get_settings
from .singleton import singleton
from .tmdb import ThingType, get_external_ids
from .types import ImdbId, TmdbId

logger = logging.getLogger(__name__)


@singleton
@trace
def get_plex(settings: Annotated[Settings, Depends(get_settings)]) -> PlexServer:
    assert 'PYTEST_CURRENT_TEST' in os.environ or X_PLEX_ENABLE_FAST_CONNECT
    acct = MyPlexAccount(token=settings.plex_token.get_secret_value())
    novell = trace(acct.resource)('Novell')
    novell.connections = [c for c in novell.connections if not c.local]
    return trace(novell.connect)(ssl=True)


async def gracefully_get_plex(request: Request, settings: Settings) -> PlexServer:
    records: list[logging.LogRecord] = []
    try:
        token = local_appender.set(records)
        return await wait_for(get_plex(request, settings), timeout=25)
    except Exception as exc:
        local_appender.reset(token)
        logger.exception('Error getting plex server', exc_info=exc)
        raise HTTPException(
            500,
            {
                'error': 'Error getting plex server',
                'details': repr(exc),
                'type': exc.__class__.__name__,
                'records': [record.getMessage() for record in records],
            },
        ) from exc


def build_agent_guid(scheme: str, id: ImdbId | TmdbId) -> str:
    return build_guid(f'com.plexapp.agents.{scheme}', id)


def build_guid(scheme: str, id: ImdbId | TmdbId) -> str:
    return str(
        URL.build(
            scheme=scheme,
            host=str(id),
        )
    )


def build_search_guid(
    plex: PlexServer, section_name: str
) -> Callable[[str], tuple[str, Video | None]]:
    def real_search(original_guid: str) -> tuple[str, Video | None]:
        guid = original_guid
        if not guid.startswith('plex://'):
            res = single(dummy.matches(agent=agent, title=guid.replace('://', '-')))
            if not res:
                return original_guid, None
            guid = res.guid

        return (original_guid, section.getGuid(guid))

    section = plex.library.section(section_name)
    dummy = section.search(maxresults=1)[0]
    agent = section.agent
    return real_search


@trace
async def get_imdb_in_plex(
    type: ThingType,
    tmdb_id: TmdbId,
    plex: PlexServer,
) -> dict[str, Video | None]:
    external_ids = await get_external_ids(type, tmdb_id)
    guids = [
        build_guid("tmdb", tmdb_id),
        build_guid("imdb", external_ids.imdb_id),
    ]
    if getattr(external_ids, 'tvdb_id', None):
        guids.append(build_guid("tvdb", external_ids.tvdb_id))

    section = 'Movies' if type == 'movie' else 'TV Shows'

    search_guid = await run_in_threadpool(build_search_guid, plex, section)

    return dict(await gather(*[run_in_threadpool(search_guid, guid) for guid in guids]))


def single[T](items: Sequence[T]) -> T | None:
    return items[0] if items else None


def make_plex_url(server_id: str, rating_key: int) -> str:
    return str(
        URL('https://app.plex.tv/desktop').with_fragment(
            f'!/server/{server_id}/details?'
            + urlencode({'key': f'/library/metadata/{rating_key}'})
        )
    )
