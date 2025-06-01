import asyncio
from collections.abc import Callable, Coroutine, MutableMapping
from dataclasses import dataclass
from functools import partial
from typing import Any, ParamSpec, TypeVar, cast

from asyncache import IdentityFunction
from asyncache import cached as _cached
from cachetools.func import lru_cache as _lru_cache
from cachetools.func import ttl_cache as _ttl_cache

T = TypeVar('T')
P = ParamSpec('P')
_caches: set[Callable[..., Any]] = set()


def lru_cache(maxsize: int | None = None) -> IdentityFunction:
    def wrapper(func: Callable[P, T]) -> Callable[P, T]:
        cache = _lru_cache(maxsize)(func)
        _caches.add(cache)
        return cache

    return wrapper


def ttl_cache(maxsize: int | None = None) -> IdentityFunction:
    def wrapper(func: Callable[P, T]) -> Callable[P, T]:
        cache = _ttl_cache(maxsize)(func)
        _caches.add(cache)
        return cache

    return wrapper


def cached(cache: MutableMapping[Any, Any]) -> IdentityFunction:
    def wrapper(func: Callable[P, T]) -> Callable[P, T]:
        c = _cached(cache)(func)
        _caches.add(c)
        return cast(Callable[P, T], c)

    return wrapper


def cache_clear() -> None:
    for c in _caches:
        c()


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
    reason: str | Exception
    task: asyncio.Task[Any]


def _callback(send: Callable[[Message], None], fut: asyncio.Task[Any]) -> None:
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
    coro: Coroutine[None, None, T], send: Callable[[Message], None]
) -> asyncio.Future[T]:
    future = asyncio.ensure_future(coro)
    future.add_done_callback(partial(_callback, send))
    return future
