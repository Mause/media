import inspect
from asyncio import iscoroutinefunction
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from contextvars import ContextVar
from typing import Any

from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.dependencies.utils import solve_dependencies
from fastapi.routing import get_dependant, run_endpoint_function
from makefun import add_signature_parameters, create_function
from starlette.middleware.base import RequestResponseEndpoint

request_var = ContextVar[Request | WebSocket]('request_var')


async def get[T](
    app: FastAPI, func: Callable[..., T], request: Request | None = None
) -> T:
    if func in app.dependency_overrides:
        func = app.dependency_overrides[func]

    dependant = get_dependant(call=func, path='')
    request = request or Request(
        {'type': 'http', 'query_string': '', 'headers': [], 'app': app}
    )

    solved = await solve_dependencies(
        request=request,
        dependant=dependant,
        dependency_overrides_provider=app,
        async_exit_stack=AsyncExitStack(),
        embed_body_fields=False,
    )

    assert not solved.errors, solved.errors

    return await run_endpoint_function(
        dependant=dependant,
        values=solved.values,
        is_coroutine=iscoroutinefunction(func),
    )


def async_value[T](value: T) -> Callable[[], Awaitable[T]]:
    async def _inner() -> T:
        return value

    return _inner


def singleton(func: Callable):  # noqa: ANN201
    async def wrapper(request: Request, **kwargs: Any) -> Any:
        app = request.app

        value = app.dependency_overrides.get(wrapper)
        if not value:
            value = await run_endpoint_function(
                dependant=get_dependant(call=func, path=''),
                values=kwargs,
                is_coroutine=iscoroutinefunction(func),
            )

            app.dependency_overrides[wrapper] = async_value(value)
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


async def store_request(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    token = request_var.set(request)
    try:
        return await call_next(request)
    finally:
        request_var.reset(token)
