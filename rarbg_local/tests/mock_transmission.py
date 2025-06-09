import logging
from itertools import count
from typing import Any
from urllib.parse import parse_qsl, urlparse
from uuid import uuid4

from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

id_iter = iter(count())
app = Flask(__name__)


def get_session():
    return '', 409, {'x-transmission-session-id': uuid4().hex}


def torrent_get(fields: dict[str, Any] | None = None, ids: set[str] | None = None):
    return jsonify({'arguments': {'torrents': []}})


def torrent_add(filename, **kwargs):
    xt = dict(parse_qsl(urlparse(filename).query))['xt']

    _, hash_ = xt.rsplit(':', 1)

    torrent = {'id': next(id_iter), 'hashString': hash_}
    return {'arguments': {'torrent-added': torrent}}


@app.route('/transmission/rpc', methods=['POST', 'GET'])
def rpc():
    if request.method == 'GET':
        return '', 200, {'is-mock': True}

    js = request.get_json()
    method = js['method']
    arguments = js.get('arguments', {})

    logger.info('Received method: %s %s', method, arguments)

    return globals()[method.replace('-', '_')](**arguments)


if __name__ == '__main__':
    app.run(debug=True, port=9091)
