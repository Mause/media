from typing import Annotated
from urllib.parse import urlencode

from fastapi import Depends
from plexapi.media import Media
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from sentry_sdk import trace

from .settings import Settings, get_settings
from .singleton import singleton
from .types import ImdbId


@singleton
@trace
def get_plex(settings: Annotated[Settings, Depends(get_settings)]) -> PlexServer:
    acct = MyPlexAccount(token=settings.plex_token.get_secret_value())
    novell = trace(acct.resource)('Novell')
    novell.connections = [c for c in novell.connections if not c.local]
    return trace(novell.connect)(ssl=True)


@trace
def get_imdb_in_plex(imdb_id: ImdbId, plex: PlexServer) -> Media | None:
    guid = f"com.plexapp.agents.imdb://{imdb_id}?lang=en"
    items = trace(plex.library.search)(guid=guid)
    return items[0] if items else None


def make_plex_url(server_id: str, dat: Media) -> str:
    return f'https://app.plex.tv/desktop#!/server/{server_id}/details?' + urlencode(
        {'key': f'/library/metadata/{dat.ratingKey}'}
    )
