import json
import logging
import os
import re
import string
from collections import defaultdict
from concurrent.futures._base import TimeoutError as FutureTimeoutError
from enum import Enum
from functools import lru_cache, wraps
from itertools import chain
from os.path import join
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple, TypeVar, cast
from urllib.parse import urlencode

from fastapi.exceptions import HTTPException
from flask import (
    Blueprint,
    Flask,
    Response,
    current_app,
    g,
    get_flashed_messages,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_admin import Admin
from flask_cors import CORS
from flask_restx import Api, Resource
from flask_restx.reqparse import RequestParser
from flask_socketio import SocketIO, send
from flask_user import UserManager, login_required, roles_required
from marshmallow.exceptions import ValidationError
from plexapi.media import Media
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from requests.exceptions import ConnectionError
from sqlalchemy import event, func
from sqlalchemy.orm.session import make_transient
from werkzeug.exceptions import NotFound
from werkzeug.wrappers import Response as WResponse

from .admin import DownloadAdmin, RoleAdmin, UserAdmin
from .auth import auth_hook
from .db import (
    Download,
    EpisodeDetails,
    MovieDetails,
    Role,
    User,
    create_episode,
    create_movie,
    db,
    get_episodes,
)
from .health import health
from .models import SeriesDetails
from .new import FakeBlueprint, magic
from .providers import PROVIDERS, FakeProvider, search_for_movie, search_for_tv
from .tmdb import (
    get_json,
    get_movie_imdb_id,
    get_tv_episodes,
    get_tv_imdb_id,
    resolve_id,
)
from .transmission_proxy import get_torrent, torrent_add
from .utils import as_resource, non_null, precondition

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pika").setLevel(logging.WARNING)

app = Blueprint('rarbg_local', __name__)

authorizations = {'basic': {'type': 'basic',}}
api = Api(
    prefix='/api',
    doc='/doc',
    validate=True,
    authorizations=authorizations,
    security='basic',
)

sockets = SocketIO(cors_allowed_origins='*')

K = TypeVar('K')
V = TypeVar('V')


@lru_cache()
def get_plex() -> PlexServer:
    acct = MyPlexAccount(os.environ['PLEX_USERNAME'], os.environ['PLEX_PASSWORD'])
    novell = acct.resource('Novell')
    novell.connections = [c for c in novell.connections if not c.local]
    return novell.connect(ssl=True)


def cache_busting_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename')
        if filename:
            values['_'] = int(
                os.stat(join(non_null(current_app.static_folder), filename)).st_mtime
            )
    return url_for(endpoint, **values)


def create_app(config: Dict):
    config = config if isinstance(config, dict) else {}
    enable_new = config.get('ENABLE_NEW', False)
    papp = Flask(__name__, static_folder='../app/build/static')
    papp.register_blueprint(app)
    if enable_new:
        papp.register_blueprint(FakeBlueprint(), url_prefix='/api')
    papp.config.update(
        {
            'SECRET_KEY': 'hkfircsc',
            'SQLALCHEMY_ECHO': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///'
            + str(Path(__file__).parent.parent / 'db.db'),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'TRANSMISSION_URL': 'http://novell.local:9091/transmission/rpc',
            'TORRENT_API_URL': 'https://torrentapi.org/pubapi_v2.php',
            'USER_APP_NAME': 'Media',
            'USER_CORPORATION_NAME': 'Lysdev',
            'USER_ENABLE_EMAIL': False,  # Disable email authentication
            'USER_ENABLE_USERNAME': True,  # Enable username authentication
            'USER_UNAUTHORIZED_ENDPOINT': 'rarbg_local.unauthorized',
            'RESTX_INCLUDE_ALL_MODELS': True,
            **config,
        }
    )
    db.init_app(papp)
    if not enable_new:
        api.init_app(papp)
    if not papp.config.get('TESTING', False):
        CORS(papp, supports_credentials=True)
    sockets.init_app(papp)

    if 'sqlite' in papp.config['SQLALCHEMY_DATABASE_URI']:
        engine = db.get_engine(papp, None)
        con = engine.raw_connection().connection
        import sqlite3

        try:
            con.create_collation(
                "en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1
            )
        except sqlite3.ProgrammingError as e:
            print(e)

    db.create_all(app=papp)
    UserManager(papp, db, User)
    papp.login_manager.request_loader(auth_hook)

    admin = Admin(papp, name='Media')
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(RoleAdmin(Role, db.session))
    admin.add_view(DownloadAdmin(Download, db.session))

    '''
    with papp.app_context():
        Mause = db.session.query(User).filter_by(username='Mause').one_or_none()
        if Mause:
            Mause.roles = list(set(Mause.roles) | {Roles.Admin, Roles.Member})
            db.session.commit()
    '''

    if 'sqlite' in papp.config['SQLALCHEMY_DATABASE_URI']:

        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.execute('pragma foreign_keys=ON')

        engine = db.get_engine(papp, None)
        event.listen(engine, 'connect', _fk_pragma_on_connect)
        _fk_pragma_on_connect(engine, None)

    return papp


@app.route('/user/unauthorized')
def unauthorized():
    if get_flashed_messages():
        return render_template('unauthorized.html')
    else:
        return redirect(url_for('.serve_index'))


@app.before_request
def before():
    if not request.path.startswith(('/user', '/manifest.json')):
        return login_required(roles_required('Member')(lambda: None))()


@app.route('/')
@app.route('/<path:path>')
def serve_index(path=None):
    if path:
        try:
            return send_from_directory('../app/build/', path)
        except NotFound:
            pass

    return send_from_directory('../app/build/', 'index.html')


def eventstream(func: Callable):
    @wraps(func)
    def decorator(*args, **kwargs):
        def default(obj):
            if isinstance(obj, Enum):
                return obj.name

            raise Exception()

        return Response(
            chain(
                (
                    f'data: {json.dumps(rset, default=default)}\n\n'
                    for rset in func(*args, **kwargs)
                ),
                ['data:\n\n'],
            ),
            mimetype="text/event-stream",
        )

    return decorator


def query_params(validator):
    def decorator(func):
        @wraps(func)
        @api.expect(validator)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs, **validator.parse_args(strict=True))

        return wrapper

    return decorator


@api.route('/stream/<type>/<tmdb_id>')
@api.param('type', enum=['series', 'movie'])
@as_resource()
@query_params(
    RequestParser()
    .add_argument('season', type=int)
    .add_argument('episode', type=int)
    .add_argument('source', choices=[p.name for p in PROVIDERS])
)
@eventstream
def stream(type: str, tmdb_id: str, source=None, season=None, episode=None):
    if source:
        provider = next(
            (provider for provider in PROVIDERS if provider.name == source), None,
        )
        if not provider:
            return api.abort(422)
    else:
        provider = FakeProvider()

    if type == 'series':
        items = provider.search_for_tv(
            get_tv_imdb_id(tmdb_id), int(tmdb_id), season, episode
        )
    else:
        items = provider.search_for_movie(get_movie_imdb_id(tmdb_id), int(tmdb_id))

    return (item.dict() for item in items)


def _stream(type: str, tmdb_id: str, season=None, episode=None):
    if type == 'series':
        items = search_for_tv(get_tv_imdb_id(tmdb_id), int(tmdb_id), season, episode)
    else:
        items = search_for_movie(get_movie_imdb_id(tmdb_id), int(tmdb_id))

    return (item.dict() for item in items)


@sockets.on('message')
def socket_stream(message):
    request = json.loads(message)

    for item in _stream(**request):
        send(json.dumps(item, default=lambda enu: enu.name))


@app.route('/delete/<type>/<id>')
def delete(type: str, id: str) -> WResponse:
    return magic()


def categorise(string: str) -> str:
    if string.startswith('Movies/'):
        return string[7:]
    elif string.startswith('Movs/'):
        return string[5:]
    else:
        return string


full_marker_re = re.compile(r'(S(\d{2})E(\d{2}))')
partial_marker_re = re.compile(r'(S(\d{2}))')
season_re = re.compile(r'\W(S\d{2})\W')
punctuation_re = re.compile(f'[{string.punctuation} ]')


def normalise(episodes: List[Dict], title: str) -> Optional[str]:
    sel = full_marker_re.search(title)
    if not sel:
        sel = season_re.search(title)
        if sel:
            return title

        print('unable to find marker in', title)
        return None

    full, _, i_episode = sel.groups()

    episode = next(
        (
            episode
            for episode in episodes
            if episode['episode_number'] == int(i_episode, 10)
        ),
        None,
    )
    assert episode

    to_replace = punctuation_re.sub(' ', episode['name'])
    to_replace = '.'.join(to_replace.split())
    title = re.sub(to_replace, 'TITLE', title, re.I)

    title = title.replace(full, 'S00E00')

    return title


def extract_marker(title: str) -> Tuple[str, Optional[str]]:
    m = full_marker_re.search(title)
    if not m:
        m = partial_marker_re.search(title)
        precondition(m, f'Cannot find marker in: {title}')
        return non_null(m).group(2), None
    return cast(Tuple[str, str], tuple(m.groups()[1:]))


@api.route('/select/<tmdb_id>/season/<season>/download_all')
@as_resource()
def download_all_episodes(tmdb_id: str, season: str) -> Dict:
    return magic()


@api.route('/diagnostics')
@as_resource()
def api_diagnostics():
    return health.run()


@api.route('/openapi.json')
@as_resource()
def api_openapi():
    return magic()


@api.route('/download')
@as_resource({'POST'})
def api_download() -> str:
    return magic()


monitor = api.namespace('monitor', 'Contains media monitor resources')


@monitor.route('')
class MonitorsResource(Resource):
    def post(self):
        return magic()

    def get(self):
        return magic()


@monitor.route('/<int:ident>')
class MonitorResource(Resource):
    def delete(self, ident: int):
        return magic()


def add_single(
    *,
    magnet: str,
    subpath: str,
    is_tv: bool,
    imdb_id: str,
    tmdb_id: int,
    season: Optional[str],
    episode: Optional[str],
    title: str,
    show_title: Optional[str],
) -> None:
    res = torrent_add(magnet, subpath)
    arguments = res['arguments']
    print(arguments)
    if not arguments:
        # the error result shape is really weird
        raise ValidationError(res['result'], data={'message': res['result']})

    transmission_id = (
        arguments['torrent-added']
        if 'torrent-added' in arguments
        else arguments['torrent-duplicate']
    )['hashString']

    already = (
        db.session.query(Download)
        .filter_by(transmission_id=transmission_id)
        .one_or_none()
    )

    print('already', already)
    if not already:
        if is_tv:
            precondition(season, 'Season must be provided for tv type')
            create_episode(
                transmission_id=transmission_id,
                imdb_id=imdb_id,
                season=non_null(season),
                episode=episode,
                title=title,
                tmdb_id=tmdb_id,
                show_title=non_null(show_title),
            )
        else:
            create_movie(
                transmission_id=transmission_id,
                imdb_id=imdb_id,
                tmdb_id=tmdb_id,
                title=title,
            )

        db.session.commit()


def groupby(iterable: Iterable[V], key: Callable[[V], K]) -> Dict[K, List[V]]:
    dd: Dict[K, List[V]] = defaultdict(list)
    for item in iterable:
        dd[key(item)].append(item)
    return dict(dd)


def resolve_season(episodes):
    if not (len(episodes) == 1 and episodes[0].is_season_pack()):
        return episodes

    pack = episodes[0]
    download = pack.download
    if download.added_by:
        added_by = download.added_by
        make_transient(download.added_by)
    else:
        added_by = None
    common = dict(
        imdb_id=download.imdb_id,
        type='episode',
        tmdb_id=download.tmdb_id,
        timestamp=download.timestamp,
        added_by=added_by,
    )
    return [
        EpisodeDetails(
            id=-1,
            download=Download(
                id=-1,
                transmission_id=f'{download.transmission_id}.{episode["episode_number"]}',
                title=episode['name'],
                **common,
            ),
            season=pack.season,
            episode=episode['episode_number'],
            show_title=pack.show_title,
        )
        for episode in get_tv_episodes(pack.download.tmdb_id, pack.season)['episodes']
    ]


def resolve_show(show: List[EpisodeDetails]) -> Dict[str, List[EpisodeDetails]]:
    seasons = groupby(show, lambda episode: episode.season)
    return {
        str(number): resolve_season(
            sorted(season, key=lambda episode: episode.episode or -1)
        )
        for number, season in seasons.items()
    }


def make_series_details(imdb_id, show: List[EpisodeDetails]) -> SeriesDetails:
    ep = show[0]
    d = ep.download

    return SeriesDetails(
        title=ep.show_title,
        seasons=resolve_show(show),
        imdb_id=d.imdb_id,
        tmdb_id=d.tmdb_id or resolve_id(imdb_id, 'tv'),
    )


def resolve_series() -> List[SeriesDetails]:
    episodes = get_episodes()

    return [
        make_series_details(imdb_id, show)
        for imdb_id, show in groupby(
            episodes, lambda episode: episode.download.tmdb_id
        ).items()
    ]


@api.route('/index')
@as_resource()
def api_index():
    return magic()


@api.route('/stats')
@as_resource()
def api_stats():
    return magic()


def get_imdb_in_plex(imdb_id: str) -> Optional[Media]:
    guid = f"com.plexapp.agents.imdb://{imdb_id}?lang=en"
    items = get_plex().library.search(guid=guid)
    return items[0] if items else None


@api.route('/movie/<int:tmdb_id>')
@as_resource()
def api_movie(tmdb_id: str):
    return magic()


tv_ns = api.namespace('tv')


@tv_ns.route('/<int:tmdb_id>')
@as_resource()
def api_tv():
    return magic()


@tv_ns.route('/<int:tmdb_id>/season/<int:season>')
@as_resource()
def api_tv_season():
    return magic()


@api.route('/torrents')
@as_resource()
def api_torrents():
    return magic()


@api.route('/search')
@as_resource()
def api_search():
    return magic()


def get_keyed_torrents() -> Dict[str, Dict]:
    if hasattr(g, 'get_keyed_torrents'):
        return g.get_keyed_torrents
    else:
        g.get_keyed_torrents = _get_keyed_torrents()
        return g.get_keyed_torrents


def _get_keyed_torrents() -> Dict[str, Dict]:
    try:
        return {t['hashString']: t for t in get_torrent()['arguments']['torrents']}
    except (ConnectionError, TimeoutError, FutureTimeoutError,) as e:
        logging.exception('Unable to connect to transmission')
        error = 'Unable to connect to transmission: ' + str(e)
        raise HTTPException(500, error)


@app.route('/redirect/plex/<tmdb_id>')
def redirect_to_plex(tmdb_id: str):
    dat = get_imdb_in_plex(tmdb_id)
    if not dat:
        return api.abort(404, 'Not found in plex')

    server_id = get_plex().machineIdentifier

    return redirect(
        f'https://app.plex.tv/desktop#!/server/{server_id}/details?'
        + urlencode({'key': f'/library/metadata/{dat.ratingKey}'})
    )


@app.route('/redirect/<type_>/<ident>')
@app.route('/redirect/<type_>/<ident>/<season>/<episode>')
def redirect_to_imdb(type_: str, ident: str, season: str = None, episode: str = None):
    if type_ == 'movie':
        imdb_id = get_movie_imdb_id(ident)
    elif season:
        imdb_id = get_json(
            f'tv/{ident}/season/{season}/episode/{episode}/external_ids'
        )['imdb_id']
    else:
        imdb_id = get_tv_imdb_id(ident)

    return redirect(f'https://www.imdb.com/title/{imdb_id}')
