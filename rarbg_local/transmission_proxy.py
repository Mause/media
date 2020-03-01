from functools import lru_cache
from typing import TYPE_CHECKING

from .client import get_client

if TYPE_CHECKING:
    from .transmission import *
else:
    transmission = lru_cache()(get_client)

    def __getattr__(name):
        return lambda *args, **kwargs: getattr(transmission(), name)(*args, **kwargs)
