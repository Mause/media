from asyncio import iscoroutinefunction
from typing import Callable, TypeVar

from fastapi import FastAPI
from fastapi.dependencies.utils import solve_dependencies
from fastapi.requests import Request
from fastapi.routing import get_dependant, run_endpoint_function

T = TypeVar('T')


async def get(app: FastAPI, func: Callable[..., T]) -> T:
    dependant = get_dependant(call=func, path='')
    request = Request(
        {'type': 'http', 'query_string': '', 'headers': [], 'app': app}, None, None
    )

    values, errors, *_ = await solve_dependencies(
        request=request, dependant=dependant, dependency_overrides_provider=app,
    )

    assert not errors

    return await run_endpoint_function(
        dependant=dependant, values=values, is_coroutine=iscoroutinefunction(func)
    )


def singleton(app: FastAPI) -> Callable:
    def decorator(func: Callable):
        @app.on_event('startup')
        async def startup():
            value = await get(app, func)

            app.dependency_overrides[func] = lambda: value

        return func

    return decorator
