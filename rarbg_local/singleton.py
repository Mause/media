import inspect
from asyncio import iscoroutinefunction
from contextlib import AsyncExitStack
from typing import Callable, Optional, TypeVar

from fastapi import FastAPI
from fastapi.dependencies.utils import solve_dependencies
from fastapi.requests import Request
from fastapi.routing import get_dependant, run_endpoint_function
from makefun import add_signature_parameters, create_function

T = TypeVar('T')


async def get(
    app: FastAPI, func: Callable[..., T], request: Optional[Request] = None
) -> T:
    dependant = get_dependant(call=func, path='')
    request = request or Request(
        {'type': 'http', 'query_string': '', 'headers': [], 'app': app}
    )

    values, errors, *_ = await solve_dependencies(
        request=request,
        dependant=dependant,
        dependency_overrides_provider=app,
        async_exit_stack=AsyncExitStack(),
    )

    assert not errors

    return await run_endpoint_function(
        dependant=dependant,
        values=values,
        is_coroutine=iscoroutinefunction(func),
    )


def singleton(func: Callable):
    async def wrapper(request: Request, **kwargs):
        app = request.app

        value = app.dependency_overrides.get(wrapper)
        if not value:
            value = await run_endpoint_function(
                dependant=get_dependant(call=func, path=''),
                values=kwargs,
                is_coroutine=iscoroutinefunction(func),
            )

            app.dependency_overrides[wrapper] = lambda: value
        else:
            value = value()

        return value

    wrapper = create_function(
        add_signature_parameters(
            inspect.signature(func),
            first=inspect.Parameter(
                'request', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request
            ),
        ),
        func_impl=wrapper,
    )

    return wrapper
