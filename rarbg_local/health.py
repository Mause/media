import aiohttp
from healthcheck import (
    Healthcheck,
    HealthcheckCallbackResponse,
    HealthcheckDatastoreComponent,
    HealthcheckStatus,
)

from .transmission_proxy import transmission

health_root = Healthcheck(name='Media')

health = HealthcheckDatastoreComponent('Root')
health_root.add_component(health)


@health.add_healthcheck
async def transmission_connectivity():
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {
            'consumers': transmission().channel.consumer_tags,
            'client_is_alive': transmission()._thread.is_alive(),
        },
    )


sources = HealthcheckDatastoreComponent('Sources')
health_root.add_component(sources)


async def check_http(url: str) -> HealthcheckCallbackResponse:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
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
    return await check_http('https://api.jikan.moe/v4')


@sources.add_healthcheck
async def katcr():
    return await check_http('https://katcr.co')


@sources.add_healthcheck
async def rarbg():
    return await check_http('https://torrentapi.org')


@sources.add_healthcheck
async def horriblesubs():
    return await check_http('https://horriblesubs.info')


@sources.add_healthcheck
async def nyaa():
    return await check_http('https://nyaa.si')


@sources.add_healthcheck
async def torrentscsv():
    return await check_http('https://torrents-csv.com')
