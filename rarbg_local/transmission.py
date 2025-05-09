from typing import Dict, Optional, TypedDict

import requests

from .utils import lru_cache

config = {'TRANSMISSION_URL': 'http://novell.local:9091/transmission/rpc'}


def get_torrent(*ids: str) -> Dict:
    call = get_session(config['TRANSMISSION_URL'])

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
            'hashString',
            # "downloadDir",
            # "uploadedEver",
            # "uploadRatio",
            # "webseedsSendingToUs",
            'files',
        ]
    }
    if ids:
        arguments["ids"] = ids

    return call("torrent-get", arguments)


class TorrentAddTorrent(TypedDict):
    hashString: str


TorrentAddArguments = TypedDict(
    'TorrentAddArguments',
    {'torrent-added': TorrentAddTorrent, 'torrent-duplicate': TorrentAddTorrent},
)


class TorrentAdd(TypedDict):
    arguments: TorrentAddArguments
    result: Optional[str]


def torrent_add(magnet: str, subpath: str) -> TorrentAdd:
    call = get_session(config['TRANSMISSION_URL'])
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
        r = session.post(url, json={'method': 'get-session'}, timeout=3)
        assert r.status_code == 409, (r, r.text, r.headers)
        session.headers[key] = r.headers[key]

    def call(method: str, arguments=None):
        r = session.post(
            url, json={'method': method, 'arguments': arguments}, timeout=3
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
