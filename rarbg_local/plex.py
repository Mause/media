from fastapi import Depends
from plexapi.media import Media
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from sentry_sdk import trace

from .settings import get_settings
from .singleton import singleton
from .types import ImdbId


@singleton
@trace
def get_plex(settings=Depends(get_settings)) -> PlexServer:
    acct = MyPlexAccount(token=settings.plex_token.get_secret_value())
    novell = trace(acct.resource)('Novell')
    novell.connections = [c for c in novell.connections if not c.local]
    return trace(novell.connect)(ssl=True)


@trace
def get_imdb_in_plex(imdb_id: ImdbId, plex) -> Media | None:
    guid = f"com.plexapp.agents.imdb://{imdb_id}?lang=en"
    items = trace(plex.library.search)(guid=guid)
    return items[0] if items else None
