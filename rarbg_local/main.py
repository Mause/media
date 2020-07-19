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
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    TypedDict,
    TypeVar,
    cast,
)
from urllib.parse import urlencode

from dataclasses_json import DataClassJsonMixin, config
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
from flask_jsontools import DynamicJSONEncoder, jsonapi
from flask_restx import Api, Resource, SchemaModel, fields
from flask_restx.reqparse import RequestParser
from flask_socketio import SocketIO, send
from flask_user import UserManager, current_user, login_required, roles_required
from marshmallow import Schema
from marshmallow import fields as mfields
from marshmallow.exceptions import ValidationError
from marshmallow.fields import String
from marshmallow.validate import Regexp as MarshRegexp
from plexapi.media import Media
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from pydantic import BaseModel
from requests.exceptions import ConnectionError, HTTPError
from sqlalchemy import event, func
from sqlalchemy.orm.session import make_transient
from werkzeug.exceptions import NotFound
from werkzeug.wrappers import Response as WResponse

from .admin import DownloadAdmin, RoleAdmin, UserAdmin
from .auth import auth_hook
from .db import (
    Download,
    EpisodeDetails,
    MediaType,
    Monitor,
    MovieDetails,
    Role,
    User,
    create_episode,
    create_movie,
    db,
    get_episodes,
    get_movies,
)
from .health import health
from .models import (
    DownloadAllResponse,
    EpisodeInfo,
    IndexResponse,
    SeriesDetails,
    StatsResponse,
)
from .new import MonitorGet, call_sync
from .providers import PROVIDERS, FakeProvider, search_for_movie, search_for_tv
from .schema import schema
from .tmdb import (
    get_json,
    get_movie,
    get_movie_imdb_id,
    get_tv,
    get_tv_episodes,
    get_tv_imdb_id,
    resolve_id,
    search_themoviedb,
)
from .transmission_proxy import get_torrent, torrent_add, transmission
from .utils import (
    as_resource,
    expect,
    non_null,
    precondition,
    schema_to_marshal,
    schema_to_openapi,
)

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


def create_app(config):
    papp = Flask(__name__, static_folder='../app/build/static')
    papp.register_blueprint(app)
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
            **(config if isinstance(config, dict) else {}),
        }
    )
    db.init_app(papp)
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

    papp.json_encoder = DynamicJSONEncoder

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
    query = db.session.query(
        EpisodeDetails if type == 'series' else MovieDetails
    ).filter_by(id=id)
    precondition(query.count() > 0, 'Nothing to delete')
    query.delete()
    db.session.commit()

    return jsonify()


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


def rewrap(schema: BaseModel) -> SchemaModel:
    s = schema.schema()
    for name, subschema in s.pop('definitions', {}).items():
        api.schema_model(name, subschema)
    return api.schema_model(schema.__name__, s)


@api.route('/select/<tmdb_id>/season/<season>/download_all')
@as_resource()
@api.response(200, 'Success', rewrap(DownloadAllResponse))
def download_all_episodes(tmdb_id: str, season: str) -> Dict:
    return call_sync(
        'GET',
        f'/select/{tmdb_id}/season/{season}/download_all',
        headers=request.headers,
    )


class ValidationErrorWrapper(Exception):
    def __init__(self, messages):
        self.messages = messages


@api.errorhandler(ValidationError)
def validation(error):
    raise ValidationErrorWrapper(error.messages)


@api.errorhandler(ValidationErrorWrapper)
def real_validation(error):
    return {'message': error.messages}, 422


@api.route('/diagnostics')
@as_resource()
def api_diagnostics():
    message, code, headers = health.run()
    return json.loads(message), code, headers


from .models import DownloadPost


@api.route('/download')
@api.response(200, 'OK', {})
@as_resource({'POST'})
@api.expect([rewrap(DownloadPost)])
def api_download() -> str:
    return call_sync('POST', '/download', headers=request.headers, body=request.data)


monitor = api.namespace('monitor', 'Contains media monitor resources')

from .models import MonitorGet, MonitorPost


@monitor.route('')
class MonitorsResource(Resource):
    @monitor.expect(rewrap(MonitorPost))
    @monitor.response(model=rewrap(MonitorGet), code=201, description='Created')
    def post(self):
        return call_sync('POST', '/monitor', '', request.headers, body=request.data)

    @monitor.response(200, 'Success', [rewrap(MonitorGet)])
    def get(self):
        return call_sync('GET', '/monitor', '', request.headers.items())


@monitor.route('/<int:ident>')
class MonitorResource(Resource):
    def delete(self, ident: int):
        query = db.session.query(Monitor).filter_by(id=ident)
        precondition(query.count() > 0, 'Nothing to delete')
        query.delete()
        db.session.commit()
        return {}


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


has_tmdb_id = api.doc(params={'tmdb_id': 'The Movie Database ID'})


@api.route('/index')
@as_resource()
@api.response(200, 'Success', rewrap(IndexResponse))
def api_index():
    return call_sync('GET', '/index', request.headers)


@api.route('/stats')
@api.response(200, 'Success', [rewrap(StatsResponse)])
@as_resource()
def api_stats():
    return call_sync('GET', '/stats', request.headers)


def get_imdb_in_plex(imdb_id: str) -> Optional[Media]:
    guid = f"com.plexapp.agents.imdb://{imdb_id}?lang=en"
    items = get_plex().library.search(guid=guid)
    return items[0] if items else None


@api.route('/movie/<int:tmdb_id>')
@as_resource()
@jsonapi
@has_tmdb_id
def api_movie(tmdb_id: str):
    movie = get_movie(tmdb_id)
    return {"title": movie['title'], "imdb_id": movie['imdb_id']}


TvResponse = api.model(
    'TvResponse',
    {
        'number_of_seasons': fields.Integer,
        'title': fields.String,
        'imdb_id': fields.String,
        'seasons': fields.List(
            fields.Nested(
                api.model(
                    'SeasonMeta',
                    {'episode_count': fields.Integer, 'season_number': fields.Integer},
                )
            )
        ),
    },
)

tv_ns = api.namespace('tv')


@tv_ns.route('/<int:tmdb_id>')
@tv_ns.response(200, 'OK', TvResponse)
@as_resource()
@tv_ns.marshal_with(TvResponse)
@has_tmdb_id
def api_tv(tmdb_id: str):
    tv = get_tv(tmdb_id)
    return {**tv, 'imdb_id': get_tv_imdb_id(tmdb_id), 'title': tv['name']}


TvSeasonResponse = tv_ns.model(
    'TvSeasonResponse',
    {
        'episodes': fields.Nested(
            tv_ns.model(
                'Episode',
                {
                    'name': fields.String,
                    'id': fields.Integer,
                    'episode_number': fields.Integer,
                    'air_date': fields.Date,
                },
            ),
            as_list=True,
        )
    },
)


@tv_ns.route('/<int:tmdb_id>/season/<int:season>')
@tv_ns.response(200, 'OK', TvSeasonResponse)
@as_resource()
@tv_ns.marshal_with(TvSeasonResponse)
@has_tmdb_id
def api_tv_season(tmdb_id: str, season: str):
    return get_tv_episodes(tmdb_id, season)


InnerTorrent = api.model(
    'InnerTorrent',
    {
        'eta': fields.Integer,
        'hashString': fields.String,
        'id': fields.Integer,
        'percentDone': fields.Float,
        'files': fields.List(
            fields.Nested(
                api.model(
                    'InnerTorrentFile',
                    {
                        'bytesCompleted': fields.Integer,
                        'length': fields.Integer,
                        'name': fields.String,
                    },
                )
            )
        ),
    },
)


@api.route('/torrents')
@as_resource()
@api.marshal_with(
    api.model('TorrentsResponse', {'*': fields.Wildcard(fields.Nested(InnerTorrent))})
)
def api_torrents():
    return get_keyed_torrents()


SearchResponse = api.model(
    'SearchResponse',
    {
        'title': fields.String,
        "Type": fields.String(enum=('movie', 'episode')),
        "type": fields.String(attribute='Type', enum=('movie', 'episode')),
        "Year": fields.Integer,
        "year": fields.Integer(attribute='Year'),
        "imdbID": fields.Integer,
    },
)


@api.route('/search')
@api.response(200, 'OK', [SearchResponse])
@as_resource()
@api.marshal_with(SearchResponse, as_list=True)
@query_params(
    RequestParser().add_argument(
        'query', type=str, help='Search query', location='args', required=True
    )
)
def api_search(query: str):
    return search_themoviedb(query)


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
        return api.abort(500, error)


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
