import logging
from typing import Annotated

from aiocache import Cache
from fastapi import Depends,

from .settings import Settings, get_settings


async def get_cache(settings: Annotated[Settings, Depends(get_settings)]) -> Cache:
    return Cache.from_url(settings.cache_url)
