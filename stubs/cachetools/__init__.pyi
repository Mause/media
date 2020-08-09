from typing import TypeVar

T = TypeVar('T')


class TTLCache():
    def __init__(self, maxsize=None, ttl=None): ...
    def __getitem__(self, name) -> T: ...
    def __contains__(self, name) -> bool: ...
    def __setitem__(self, name, value: T): ...