from pathlib import Path
from typing import Annotated

from pydantic import AnyUrl, SecretStr
from pydantic_settings import BaseSettings

from .singleton import singleton


class Settings(BaseSettings):
    root: Path = Path(__file__).parent.parent.absolute()
    database_url: str = f"sqlite:///{root}/db.db"
    static_resources_path: Path = root / 'app/build'
    transmission_url: Annotated[str, AnyUrl] = 'http://localhost:9091'
    '''
    TODO: use this
    '''
    plex_token: SecretStr
    cache_url: Annotated[str, AnyUrl] = 'memory://'


@singleton
async def get_settings() -> Settings:
    return Settings()
