import requests
from healthcheck import HealthCheck

from .transmission_proxy import transmission

health = HealthCheck(success_handler=lambda a: a, failure_handler=lambda a: a)


@health.add_check
def transmission_connectivity():
    return (
        True,
        {
            'consumers': transmission().channel.consumer_tags,
            'client_is_alive': transmission()._thread.is_alive(),
        },
    )


@health.add_check
def jikan():
    return True, requests.get('https://api.jikan.moe/v4').json()


@health.add_check
def katcr():
    res = requests.head('https://katcr.co')
    res.raise_for_status()
    return True, repr(res)


@health.add_check
def rarbg():
    res = requests.head('https://torrentapi.org')
    res.raise_for_status()
    return True, repr(res)


@health.add_check
def horriblesubs():
    res = requests.head('https://horriblesubs.info')
    res.raise_for_status()
    return True, repr(res)


@health.add_check
def nyaa():
    res = requests.head('https://nyaa.si')
    res.raise_for_status()
    return True, repr(res)


@health.add_check
def torrentscsv():
    res = requests.head('https://torrents-csv.com')
    res.raise_for_status()
    return True, repr(res)
