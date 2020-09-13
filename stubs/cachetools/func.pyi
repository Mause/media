from typing import TypeVar, Callable

T = TypeVar('T')

def ttl_cache() -> Callable[[Callable[..., T]], Callable[..., T]]: ...
