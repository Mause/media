from typing import Callable, TypeVar

T = TypeVar('T')

def ttl_cache() -> Callable[[Callable[..., T]], Callable[..., T]]: ...
