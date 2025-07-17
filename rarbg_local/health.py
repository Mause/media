import contextvars
import logging
from collections.abc import Callable, Coroutine
from datetime import datetime
from os import getpid
from typing import Any, cast, overload

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from healthcheck import (
    Healthcheck,
    HealthcheckCallbackResponse,
    HealthcheckDatastoreComponent,
    HealthcheckHTTPComponent,
    HealthcheckInternalComponent,
    HealthcheckStatus,
)
from healthcheck.healthcheck import HealthcheckComponentInterface
from healthcheck.models import ComponentType
from plexapi.server import PlexServer
from pydantic import BaseModel, RootModel
from sqlalchemy.sql import text

from .config import commit
from .db import get_async_sessionmaker
from .plex import get_plex
from .singleton import get as _get
from .transmission_proxy import transmission

logger = logging.getLogger(__name__)
router = APIRouter(tags=['diagnostics'])
request_var = contextvars.ContextVar[Request]('request_var')


@overload
async def get[T](dependent: Callable[..., Coroutine[Any, Any, T]]) -> T: ...


@overload
async def get[T](dependent: Callable[..., T]) -> T: ...


async def get(dependent):
    return await _get(request_var.get().app, dependent, request_var.get())


def build() -> Healthcheck:
    def add_component(
        decl: HealthcheckComponentInterface,
        check: Callable[[], Coroutine[Any, Any, HealthcheckCallbackResponse]],
    ) -> HealthcheckComponentInterface:
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
    add_component(HealthcheckInternalComponent('client_ip'), client_ip)

    return health


class DiagnosticsRoot(BaseModel):
    version: str
    checks: list[str]


@router.get('')
async def diagnostics() -> DiagnosticsRoot:
    return DiagnosticsRoot(
        version=commit or 'dev', checks=[comp.name for comp in build().components]
    )


class HealthcheckResponse(BaseModel):
    model_config = {'from_attributes': True}

    component_name: str
    component_type: ComponentType
    status: HealthcheckStatus
    time: datetime
    output: Any


class HealthcheckResponses(RootModel[list[HealthcheckResponse]]):
    pass


@router.get('/{component_name}')
async def component_diagnostics(
    request: Request, component_name: str
) -> HealthcheckResponses:
    health = build()
    component = next(
        (comp for comp in health.components if comp.name == component_name), None
    )
    if component is None:
        raise HTTPException(404, ({'error': 'Component not found'}))

    request_var.set(request)

    return HealthcheckResponses.model_validate(await component.run())


async def check_database() -> HealthcheckCallbackResponse:
    Session = await get(get_async_sessionmaker)

    async with Session() as session:
        res = await session.execute(
            text(
                'SELECT SQLITE_VERSION()'
                if session.sync_session.bind.name == 'sqlite'
                else 'SELECT version()'
            )
        )

        return HealthcheckCallbackResponse(
            HealthcheckStatus.PASS,
            {  # type: ignore[arg-type]
                'version': res.scalar(),
            },
        )


async def pool() -> HealthcheckCallbackResponse:
    def pget(field: str) -> int:
        value = getattr(pool, field, None)

        return cast(int, value() if callable(value) else value)

    sessionlocal = await get(get_async_sessionmaker)

    pool = sessionlocal.kw['bind'].pool
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {  # type: ignore[arg-type]
            'worker_id': getpid(),
            'size': pget('size'),
            'checkedin': pget('checkedin'),
            'overflow': pget('overflow'),
            'checkedout': pget('checkedout'),
        },
    )


async def client_ip() -> HealthcheckCallbackResponse:
    from .providers import serpapi

    request = request_var.get()

    ip_address = request.headers.get(
        'x-forwarded-for', request.client.host if request.client else None
    )

    if not ip_address:
        return HealthcheckCallbackResponse(
            HealthcheckStatus.FAIL,
            {  # type: ignore[arg-type]
                'error': 'No IP address found in request headers'
            },
        )

    location = None
    age = None
    try:
        location = await run_in_threadpool(
            serpapi.resolve_location,
            ip_address,
        )
        age = await run_in_threadpool(serpapi.get_age)
    except Exception as e:
        logger.exception('Error resolving location for IP %s: %s', ip_address, e)

    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {  # type: ignore[arg-type]
            'x-forwarded-for': request.headers.get('x-forwarded-for', 'unknown'),
            'remote_addr': request.client.host if request.client else 'unknown',
            'location': location or 'unknown',
            'age': age or 'unknown',
        },
    )


async def transmission_connectivity() -> HealthcheckCallbackResponse:
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {  # type: ignore[arg-type]
            'consumers': transmission().channel.consumer_tags,
            'client_is_alive': transmission()._thread.is_alive(),
        },
    )


async def plex_connectivity() -> HealthcheckCallbackResponse:
    plex: PlexServer = await get(get_plex)
    return HealthcheckCallbackResponse(HealthcheckStatus.PASS, plex._baseurl)
