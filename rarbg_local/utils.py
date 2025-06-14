import asyncio
from collections.abc import Callable, Coroutine, MutableMapping
from dataclasses import dataclass
from functools import partial
from typing import Any, Protocol, cast, runtime_checkable

from asyncache import cached as _cached
from cachetools.func import lru_cache as _lru_cache
from cachetools.func import ttl_cache as _ttl_cache


@runtime_checkable
class Cache(Protocol):
    def clear(self) -> None: ...


type IdentityFunction[T] = Callable[[T], T]

_caches: list[Cache] = []


def _append(t: object) -> None:
    assert isinstance(t, Cache)
    _caches.append(t)


def lru_cache(maxsize: int | None = None) -> IdentityFunction:
    def wrapper[T, **P](func: Callable[P, T]) -> Callable[P, T]:
        cache = _lru_cache(maxsize)(func)
        _append(cache)
        return cache

    return wrapper


def ttl_cache(maxsize: int | None = None) -> IdentityFunction:
    def wrapper[T, **P](func: Callable[P, T]) -> Callable[P, T]:
        cache = _ttl_cache(maxsize)(func)
        _append(cache)
        return cache

    return wrapper


def cached(cache: MutableMapping[Any, Any]) -> IdentityFunction:
    def wrapper[T, **P](func: Callable[P, T]) -> Callable[P, T]:
        c = _cached(cache)(func)
        _append(cache)
        return cast(Callable[P, T], c)

    return wrapper


def cache_clear() -> None:
    for c in _caches:
        c.clear()


class NullPointerException(Exception):
    pass


def non_null[T](thing: T | None) -> T:
    if not thing:
        raise NullPointerException()
    return thing


def precondition[T](res: T | None, message: str) -> T:
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


def create_monitored_task[T](
    coro: Coroutine[None, None, T], send: Callable[[Message], None]
) -> asyncio.Future[T]:
    future = asyncio.ensure_future(coro)
    future.add_done_callback(partial(_callback, send))
    return future


def format_marker(season: int, episode: int | None) -> str:
    return f'S{season:02d}E{episode:02d}' if episode else f'S{season:02d}'
