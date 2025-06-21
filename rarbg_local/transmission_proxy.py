import os
from collections.abc import Callable
from functools import lru_cache
from typing import TYPE_CHECKING

from mause_rpc.client import Client, get_client
from pika.connection import URLParameters

transmission: Callable[[], Client]

if TYPE_CHECKING:
    from .transmission import get_torrent, torrent_add
else:
    transmission = lru_cache(
        lambda: get_client(
            'rpc.server.queue', URLParameters(os.environ['CLOUDAMQP_URL'])
        )
    )

    def __getattr__(name: str) -> Callable:
        return lambda *args, **kwargs: getattr(transmission(), name)(*args, **kwargs)


__all__ = ['torrent_add', 'get_torrent']
