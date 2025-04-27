import requests
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
    breakpoint()
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS,
        {
            'consumers': transmission().channel.consumer_tags,
            'client_is_alive': transmission()._thread.is_alive(),
        },
    )


@health.add_healthcheck
async def jikan():
    return HealthcheckCallbackResponse(
        HealthcheckStatus.PASS, requests.get('https://api.jikan.moe/v4').json()
    )


sources = HealthcheckDatastoreComponent('Sources')
health_root.add_component(sources)


@sources.add_healthcheck
async def katcr():
    res = requests.head('https://katcr.co')
    res.raise_for_status()
    return HealthcheckCallbackResponse(HealthcheckStatus.PASS, repr(res))


@sources.add_healthcheck
async def rarbg():
    res = requests.head('https://torrentapi.org')
    res.raise_for_status()
    return HealthcheckCallbackResponse(HealthcheckStatus.PASS, repr(res))


@sources.add_healthcheck
async def horriblesubs():
    res = requests.head('https://horriblesubs.info')
    res.raise_for_status()
    return HealthcheckCallbackResponse(HealthcheckStatus.PASS, repr(res))


@sources.add_healthcheck
async def nyaa():
    res = requests.head('https://nyaa.si')
    res.raise_for_status()
    return HealthcheckCallbackResponse(HealthcheckStatus.PASS, repr(res))


@sources.add_healthcheck
async def torrentscsv():
    res = requests.head('https://torrents-csv.com')
    res.raise_for_status()
    return HealthcheckCallbackResponse(HealthcheckStatus.PASS, repr(res))
