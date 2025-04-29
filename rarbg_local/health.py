import contextvars
from datetime import datetime
from functools import partial
from os import getpid
from typing import Any, Callable, List, TypeVar
from urllib.parse import urlparse

import aiohttp
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
from pydantic import BaseModel
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from .db import get_session_local
from .settings import get_settings
from .singleton import get as _get
from .transmission_proxy import transmission

router = APIRouter()
request_var = contextvars.ContextVar[Request]('request_var')
health = Healthcheck(name='Media')
T = TypeVar('T')


async def get(dependent: Callable[..., T]) -> T:
    return await _get(request_var.get().app, dependent, request_var.get())


def add_component(decl):
    health.add_component(decl)
    return decl.add_healthcheck


@router.get('', response_model=List[str])
async def diagnostics():
    return [comp.name for comp in health.components]


class HealthcheckResponse(BaseModel):
    class Config:
        orm_mode = True

    component_name: str
    component_type: ComponentType
    status: HealthcheckStatus
    time: datetime
    output: Any


@router.get('/{component_name}', response_model=List[HealthcheckResponse])
async def component_diagnostics(request: Request, component_name: str):
    component = next(
        (comp for comp in health.components if comp.name == component_name), None
    )
    if component is None:
        return JSONResponse({'error': 'Component not found'}, status_code=404)

    request_var.set(request)

    return await component.run()


@add_component(HealthcheckDatastoreComponent('database'))
async def check_database():
    settings = await get(get_settings)

    url = make_url(settings.database_url)
    is_sqlite = url.drivername == 'sqlite'
    if is_sqlite:
        url = url.set(drivername='sqlite+aiosqlite')
    else:
        url = url.set(drivername='postgresql+asyncpg')
    engine = create_async_engine(url)

    async with engine.connect() as conn:
        res = await conn.execute(
            text('SELECT SQLITE_VERSION()' if is_sqlite else 'SELECT version()')
        )

        return HealthcheckCallbackResponse(
            HealthcheckStatus.PASS,
            {
                'version': res.scalar(),
            },
        )


@add_component(HealthcheckDatastoreComponent('pool'))
async def pool():
    def get(field):
        value = getattr(pool, field, None)

        return value() if callable(value) else value

    sessionlocal = await get(get_session_local)

    pool = sessionlocal.kw['bind'].pool
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {
            'worker_id': getpid(),
            'size': get('size'),
            'checkedin': get('checkedin'),
            'overflow': get('overflow'),
            'checkedout': get('checkedout'),
        },
    )


@add_component(HealthcheckInternalComponent('transmission'))
async def transmission_connectivity():
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {
            'consumers': transmission().channel.consumer_tags,
            'client_is_alive': transmission()._thread.is_alive(),
        },
    )


async def check_http(method: str, url: str) -> HealthcheckCallbackResponse:
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url) as response:
            if response.status == 200:
                return HealthcheckCallbackResponse(
                    HealthcheckStatus.PASS, repr(response)
                )
            else:
                return HealthcheckCallbackResponse(
                    HealthcheckStatus.FAIL, f'Failed to reach {url}: {response.status}'
                )


def generate_check_http(method: str, url: str):
    parsed_url = urlparse(url)
    add_component(HealthcheckHTTPComponent(parsed_url.netloc))(
        partial(check_http, method, url)
    )


generate_check_http('GET', 'https://api.jikan.moe/v4')
generate_check_http('HEAD', 'https://katcr.co')
generate_check_http('HEAD', 'https://torrentapi.org')
generate_check_http('HEAD', 'https://horriblesubs.info')
generate_check_http('HEAD', 'https://nyaa.si')
generate_check_http('HEAD', 'https://torrents-csv.com')
