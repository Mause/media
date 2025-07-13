from asyncio import gather
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.video import Video
from sentry_sdk import trace
from yarl import URL

from .settings import Settings, get_settings
from .singleton import singleton
from .tmdb import ThingType, get_external_ids
from .types import ImdbId, TmdbId


@singleton
@trace
def get_plex(settings: Annotated[Settings, Depends(get_settings)]) -> PlexServer:
    acct = MyPlexAccount(token=settings.plex_token.get_secret_value())
    novell = trace(acct.resource)('Novell')
    novell.connections = [c for c in novell.connections if not c.local]
    return trace(novell.connect)(ssl=True)


def build_agent_guid(scheme: str, id: ImdbId | TmdbId) -> str:
    return str(URL.build(scheme=f'com.plexapp.agents.{scheme}', host=str(id)))


@trace
async def get_imdb_in_plex(
    type: ThingType,
    tmdb_id: TmdbId,
    plex: PlexServer,
) -> list[Video]:
    external_ids = await get_external_ids(type, tmdb_id)
    guids = [
        build_agent_guid("tmdb", tmdb_id),
        build_agent_guid("imdb", external_ids.imdb_id),
    ]

    search_guid = trace(plex.library.search)

    return [
        single(item)
        for item in await gather(
            *[run_in_threadpool(search_guid, guid=guid) for guid in guids]
        )
        if item
    ]


def single[T](items: Sequence[T]) -> T | None:
    return items[0] if items else None


def make_plex_url(server_id: str, rating_key: int) -> str:
    return str(
        URL('https://app.plex.tv/desktop')
        .with_fragment(f'!/server/{server_id}/details')
        .with_query(key=f'/library/metadata/{rating_key}')
    )
