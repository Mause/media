from pprint import pprint
from typing import Dict
from functools import lru_cache

import requests
from flask import current_app


def get_torrent(*ids: str) -> Dict:
    call = get_session(current_app.config['TRANSMISSION_URL'])

    arguments: Dict = {
        "fields": [
            "id",
            # "error",
            # "errorString",
            "eta",
            # "isFinished",
            # "isStalled",
            # "leftUntilDone",
            # "metadataPercentComplete",
            # "peersConnected",
            # "peersGettingFromUs",
            # "peersSendingToUs",
            "percentDone",
            # "queuePosition",
            # "rateDownload",
            # "rateUpload",
            # "recheckProgress",
            # "seedRatioMode",
            # "seedRatioLimit",
            # "sizeWhenDone",
            # "status",
            # "trackers",
            # "downloadDir",
            # "uploadedEver",
            # "uploadRatio",
            # "webseedsSendingToUs",
        ]
    }
    if ids:
        arguments["ids"] = ids

    return call("torrent-get", arguments)


def torrent_add(magnet: str, subpath: str) -> Dict:
    call = get_session(current_app.config['TRANSMISSION_URL'])
    return call(
        "torrent-add",
        {
            "paused": False,
            "download-dir": f"/media/me/raid/{subpath}",
            "filename": magnet,
        },
    )


@lru_cache()
def get_session(url):
    def refresh_session():
        key = 'X-Transmission-Session-Id'
        session.headers[key] = session.post(
            url, json={'method': 'get-session'}
        ).headers[key]

    def call(method: str, arguments=None):
        r = session.post(
            url, json={'method': method, 'arguments': arguments}
        )
        if r.status_code == 409:
            refresh_session()
            return call(method, arguments)
        if not r.ok:
            raise Exception(r.text)
        return r.json()

    session = requests.Session()
    session.auth = ('transmission', 'transmission')
    refresh_session()

    return call
