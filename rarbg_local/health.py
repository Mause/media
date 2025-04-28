import contextvars
from functools import partial
from urllib.parse import urlparse

import aiohttp
from healthcheck import (
    Healthcheck,
    HealthcheckCallbackResponse,
    HealthcheckDatastoreComponent,
    HealthcheckHTTPComponent,
    HealthcheckInternalComponent,
    HealthcheckStatus,
)
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from .transmission_proxy import transmission

database_var = contextvars.ContextVar[str]('database_var')

health = Healthcheck(name='Media')

services = HealthcheckInternalComponent('Services')
health.add_component(services)

database = HealthcheckDatastoreComponent('Database')
health.add_component(database)


@database.add_healthcheck
async def check_database():
    url = make_url(database_var.get())
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


@services.add_healthcheck
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
    health.add_component(
        HealthcheckHTTPComponent(parsed_url.netloc).add_healthcheck(
            partial(check_http, method, url)
        )
    )


generate_check_http('GET', 'https://api.jikan.moe/v4')
generate_check_http('HEAD', 'https://katcr.co')
generate_check_http('HEAD', 'https://torrentapi.org')
generate_check_http('HEAD', 'https://horriblesubs.info')
generate_check_http('HEAD', 'https://nyaa.si')
generate_check_http('HEAD', 'https://torrents-csv.com')
