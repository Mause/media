from uuid import uuid4
from itertools import count
from typing import Dict, Any, Set
from urllib.parse import urlparse, parse_qsl

from flask import Flask, request, jsonify

id_iter = iter(count())
app = Flask(__name__)


def get_session():
    return '', 200, {'x-transmission-session-id': uuid4().hex}


def torrent_get(fields: Dict[str, Any] = None, ids: Set[str] = None):
    return jsonify({'arguments': {'torrents': []}})


def torrent_add(filename, **kwargs):
    xt = dict(parse_qsl(urlparse(filename).query))['xt']

    _, hash_ = xt.rsplit(':', 1)

    torrent = {'id': next(id_iter), 'hash': hash_}
    return {'arguments': {'torrent-added': torrent}}


@app.route('/transmission/rpc', methods=['POST', 'GET'])
def rpc():
    if request.method == 'GET':
        return '', 200, {'is-mock': True}

    js = request.get_json()
    method = js['method']
    arguments = js.get('arguments', {})

    print(method, arguments)

    return globals()[method.replace('-', '_')](**arguments)


if __name__ == '__main__':
    app.run(debug=True, port=9091)
