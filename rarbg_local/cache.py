import logging
from typing import Annotated

from aiocache import Cache
from fastapi import Depends

from .settings import Settings, get_settings


async def get_cache(settings: Annotated[Settings, Depends(get_settings)]) -> Cache:
    # TODO: use context manager here to autoclose once supported
    return Cache.from_url(settings.cache_url)
