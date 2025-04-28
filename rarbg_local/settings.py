from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, SecretStr

from .singleton import singleton


class Settings(BaseSettings):
    root = Path(__file__).parent.parent.absolute()
    database_url = f"sqlite:///{root}/db.db"
    static_resources_path = root / 'app/build'
    plex_token: SecretStr


@singleton
async def get_settings():
    return Settings()
