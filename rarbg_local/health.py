import aiohttp
from healthcheck import (
    Healthcheck,
    HealthcheckCallbackResponse,
    HealthcheckHTTPComponent,
    HealthcheckInternalComponent,
    HealthcheckDatastoreComponent,
    HealthcheckStatus,
)
import contextvars

from .transmission_proxy import transmission

database_var = contextvars.ContextVar('database_var')

health = Healthcheck(name='Media')

services = HealthcheckInternalComponent('Services')
health.add_component(services)

database = HealthcheckDatastoreComponent('Database')
health.add_component(database)


@database.add_healthcheck
async def check_database():
    engine = AsyncEngine(database_var.get())

    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        await engine.query('SELECT 1')
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


sources = HealthcheckHTTPComponent('Sources')
health.add_component(sources)


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


@sources.add_healthcheck
async def jikan():
    return await check_http('GET', 'https://api.jikan.moe/v4')


@sources.add_healthcheck
async def katcr():
    return await check_http('HEAD', 'https://katcr.co')


@sources.add_healthcheck
async def rarbg():
    return await check_http('HEAD', 'https://torrentapi.org')


@sources.add_healthcheck
async def horriblesubs():
    return await check_http('HEAD', 'https://horriblesubs.info')


@sources.add_healthcheck
async def nyaa():
    return await check_http('HEAD', 'https://nyaa.si')


@sources.add_healthcheck
async def torrentscsv():
    return await check_http('HEAD', 'https://torrents-csv.com')
