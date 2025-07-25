import logging
from itertools import count
from typing import Any
from urllib.parse import parse_qsl, urlparse
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

id_iter = iter(count())
app = FastAPI()


def get_session() -> Response:
    return Response(409, headers={'x-transmission-session-id': uuid4().hex})


def torrent_get(
    fields: dict[str, Any] | None = None, ids: set[str] | None = None
) -> dict:
    return {'arguments': {'torrents': []}}


def torrent_add(filename: str) -> dict:
    xt = dict(parse_qsl(urlparse(filename).query))['xt']

    _, hash_ = xt.rsplit(':', 1)

    torrent = {'id': next(id_iter), 'hashString': hash_}
    return {'arguments': {'torrent-added': torrent}}


class Body(BaseModel):
    method: str
    arguments: dict[str, Any] = {}


@app.post('/transmission/rpc')
def rpc(js: Body) -> Any:
    method = js.method
    arguments = js.arguments

    logger.info('Received method: %s %s', method, arguments)

    match method:
        case 'torrent-add':
            return torrent_add(**arguments)
        case 'torrents-get':
            return torrent_get(**arguments)
        case 'get-session':
            return get_session()
        case _:
            raise Exception()


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app=app, port=9091)
