import contextvars
from collections.abc import Callable, Coroutine
from datetime import datetime
from os import getpid
from typing import Any, cast, overload

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from healthcheck import (
    Healthcheck,
    HealthcheckCallbackResponse,
    HealthcheckDatastoreComponent,
    HealthcheckHTTPComponent,
    HealthcheckInternalComponent,
    HealthcheckStatus,
)
from healthcheck.models import ComponentType
from plexapi.server import PlexServer
from pydantic import BaseModel
from sqlalchemy.sql import text

from .db import get_async_engine, get_session_local
from .plex import get_plex
from .singleton import get as _get
from .transmission_proxy import transmission

router = APIRouter(tags=['diagnostics'])
request_var = contextvars.ContextVar[Request]('request_var')


@overload
async def get[T](dependent: Callable[..., Coroutine[Any, Any, T]]) -> T: ...


@overload
async def get[T](dependent: Callable[..., T]) -> T: ...


async def get(dependent):
    return await _get(request_var.get().app, dependent, request_var.get())


def build():
    def add_component(decl, check):
        health.add_component(decl)
        return decl.add_healthcheck(check)

    from .providers import get_providers
    from .providers.abc import check_http

    health = Healthcheck(name='Media')
    add_component(HealthcheckDatastoreComponent('database'), check_database)
    add_component(HealthcheckDatastoreComponent('pool'), pool)
    add_component(
        HealthcheckInternalComponent('transmission'), transmission_connectivity
    )
    add_component(HealthcheckHTTPComponent('plex'), plex_connectivity)

    for provider in get_providers():
        add_component(HealthcheckHTTPComponent(provider.type.value), provider.health)

    add_component(
        HealthcheckHTTPComponent('jikan'),
        lambda: check_http('https://api.jikan.moe/v4', 'GET'),
    )

    return health


@router.get('', response_model=list[str])
async def diagnostics():
    return [comp.name for comp in build().components]


class HealthcheckResponse(BaseModel):
    model_config = {'from_attributes': True}

    component_name: str
    component_type: ComponentType
    status: HealthcheckStatus
    time: datetime
    output: Any


@router.get('/{component_name}', response_model=list[HealthcheckResponse])
async def component_diagnostics(request: Request, component_name: str):
    health = build()
    component = next(
        (comp for comp in health.components if comp.name == component_name), None
    )
    if component is None:
        return JSONResponse({'error': 'Component not found'}, status_code=404)

    request_var.set(request)

    return await component.run()


async def check_database():
    engine = await get(get_async_engine)

    async with engine.connect() as conn:
        res = await conn.execute(
            text(
                'SELECT SQLITE_VERSION()'
                if engine.name == 'sqlite'
                else 'SELECT version()'
            )
        )

        return HealthcheckCallbackResponse(
            HealthcheckStatus.PASS,
            {
                'version': res.scalar(),
            },
        )


async def pool():
    def pget(field: str) -> int:
        value = getattr(pool, field, None)

        return cast(int, value() if callable(value) else value)

    sessionlocal = await get(get_session_local)

    pool = sessionlocal.kw['bind'].pool
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {
            'worker_id': getpid(),
            'size': pget('size'),
            'checkedin': pget('checkedin'),
            'overflow': pget('overflow'),
            'checkedout': pget('checkedout'),
        },
    )


async def transmission_connectivity():
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {
            'consumers': transmission().channel.consumer_tags,
            'client_is_alive': transmission()._thread.is_alive(),
        },
    )


async def plex_connectivity() -> HealthcheckCallbackResponse:
    plex: PlexServer = await get(get_plex)
    return HealthcheckCallbackResponse(HealthcheckStatus.PASS, plex._baseurl)
