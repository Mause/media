import os
from functools import lru_cache
from typing import TYPE_CHECKING

from mause_rpc.client import get_client
from pika.connection import URLParameters

if TYPE_CHECKING:
    from .transmission import torrent_add, get_torrent
else:
    transmission = lru_cache()(
        lambda: get_client(
            'rpc.server.queue', URLParameters(os.environ['CLOUDAMQP_URL'])
        )
    )

    def __getattr__(name):
        return lambda *args, **kwargs: getattr(transmission(), name)(*args, **kwargs)


__all__ = ['torrent_add', 'get_torrent']
