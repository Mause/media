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
    requests.head('https://katcr.co')
    return True, 'kickass'


@health.add_check
def rarbg():
    requests.head('https://torrentapi.org')
    return True, 'rarbg'


@health.add_check
def horriblesubs():
    requests.head('https://horriblesubs.info')
    return True, 'horriblesubs'


@health.add_check
def nyaa():
    requests.head('https://nyaa.si').raise_for_status()
    return True, 'nyaa'


@health.add_check
def torrentscsv():
    requests.head('https://torrents-csv.com').raise_for_status()
    return True, 'torrentscsv'
