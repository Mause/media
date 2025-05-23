import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from functools import lru_cache as _lru_cache
from functools import partial
from typing import TypeVar

from asyncache import cached as _cached
from cachetools.func import ttl_cache as _ttl_cache

T = TypeVar('T')
_caches: set[Callable[[], None]] = set()


def lru_cache(*args, **kwargs):
    def wrapper(func):
        cache = _lru_cache(*args, **kwargs)(func)
        _caches.add(cache.clear)
        return cache

    return wrapper


def ttl_cache(*args, **kwargs):
    def wrapper(func):
        cache = _ttl_cache(*args, **kwargs)(func)
        _caches.add(cache.clear)
        return cache

    return wrapper


def cached(cache):
    def wrapper(func):
        c = _cached(cache)(func)
        _caches.add(cache.clear)
        return c

    return wrapper


def cache_clear():
    for cache_clear in _caches:
        cache_clear()


class NullPointerException(Exception):
    pass


def non_null(thing: T | None) -> T:
    if not thing:
        raise NullPointerException()
    return thing


def precondition(res: T | None, message: str) -> T:
    if not res:
        raise AssertionError(message)
    return res


@dataclass
class Message:
    event: str
    reason: str
    task: asyncio.Task


def _callback(send, fut):
    try:
        fut.result()
    except asyncio.CancelledError:
        send(Message("exit", "killed", fut))
        raise
    except Exception as e:
        send(Message("err", e, fut))
    else:
        send(Message("exit", "normal", fut))


def create_monitored_task(
    coro: Coroutine[None, None, T], send: Callable
) -> asyncio.Future[T]:
    future = asyncio.ensure_future(coro)
    future.add_done_callback(partial(_callback, send))
    return future
