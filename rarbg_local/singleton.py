from asyncio import iscoroutinefunction
from typing import Callable, TypeVar

from fastapi import FastAPI
from fastapi.dependencies.utils import solve_dependencies
from fastapi.requests import Request
from fastapi.routing import get_dependant, run_endpoint_function

T = TypeVar('T')


async def get(app: FastAPI, func: Callable[..., T], request: Request = None) -> T:
    dependant = get_dependant(call=func, path='')
    request = request or Request(
        {'type': 'http', 'query_string': '', 'headers': [], 'app': app}
    )

    values, errors, *_ = await solve_dependencies(
        request=request, dependant=dependant, dependency_overrides_provider=app,
    )

    assert not errors

    return await run_endpoint_function(
        dependant=dependant, values=values, is_coroutine=iscoroutinefunction(func)
    )


def singleton(func: Callable):
    async def wrapper(request: Request):
        app = request.app

        value = app.dependency_overrides.get(wrapper)
        if not value:
            value = await get(app, func)

            app.dependency_overrides[wrapper] = lambda: value
        else:
            value = value()

        return value

    return wrapper