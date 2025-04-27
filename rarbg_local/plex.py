from typing import Optional

from fastapi import Depends
from plexapi.media import Media
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

from .settings import get_settings
from .singleton import singleton


@singleton
def get_plex(settings=Depends(get_settings)) -> PlexServer:
    acct = MyPlexAccount(token=settings.plex_token.get_secret_value())
    novell = acct.resource('Novell')
    novell.connections = [c for c in novell.connections if not c.local]
    return novell.connect(ssl=True)


def get_imdb_in_plex(imdb_id: str, plex) -> Optional[Media]:
    guid = f"com.plexapp.agents.imdb://{imdb_id}?lang=en"
    items = plex.library.search(guid=guid)
    return items[0] if items else None
