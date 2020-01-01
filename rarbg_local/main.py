import inspect
import json
import logging
import re
import string
from collections import defaultdict
from concurrent.futures._base import TimeoutError as FutureTimeoutError
from functools import wraps
from itertools import chain, zip_longest
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    cast,
)
from urllib.parse import parse_qsl, urlparse

from flask import (
    Blueprint,
    Flask,
    Response,
    abort,
    current_app,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_admin import Admin
from flask_jsontools import DynamicJSONEncoder, jsonapi
from flask_login import login_user
from flask_restless import APIManager, ProcessingException
from flask_user import UserManager, current_user, login_required, roles_required
from flask_wtf import FlaskForm
from humanize import naturaldelta
from requests.exceptions import ConnectionError
from sqlalchemy import event
from werkzeug.wrappers import Response as WResponse
from wtforms import StringField
from wtforms.validators import DataRequired, Regexp

from .admin import RoleAdmin, UserAdmin
from .db import (
    Download,
    EpisodeDetails,
    MovieDetails,
    Role,
    Roles,
    User,
    create_episode,
    create_movie,
    db,
    get_episodes,
    get_movies,
)
from .frontend import e
from .rarbg import RarbgTorrent, get_rarbg, get_rarbg_iter
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
from .transmission_proxy import get_torrent, torrent_add

logging.basicConfig(level=logging.DEBUG)

app = Blueprint('rarbg_local', __name__)

K = TypeVar('K')
V = TypeVar('V')


def create_app(config):
    papp = Flask(__name__)
    papp.register_blueprint(app)
    papp.config.update(
        {
            'SECRET_KEY': 'hkfircsc',
            'SQLALCHEMY_ECHO': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.db',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'TRANSMISSION_URL': 'http://novell.local:9091/transmission/rpc',
            'TORRENT_API_URL': 'https://torrentapi.org/pubapi_v2.php',
            'USER_APP_NAME': 'Media',
            'USER_CORPORATION_NAME': 'Lysdev',
            'USER_ENABLE_EMAIL': False,  # Disable email authentication
            'USER_ENABLE_USERNAME': True,  # Enable username authentication
            'USER_UNAUTHORIZED_ENDPOINT': 'rarbg_local.unauthorized',
            **config,
        }
    )
    db.init_app(papp)
    db.create_all(app=papp)
    UserManager(papp, db, User)

    papp.json_encoder = DynamicJSONEncoder

    e.init_app(papp)

    manager = APIManager(
        papp, flask_sqlalchemy_db=db, preprocessors={'GET_MANY': [check_auth]}
    )
    manager.create_api(
        Download, collection_name='downloads', include_methods=['progress']
    )

    admin = Admin(papp, name='Media')
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(RoleAdmin(Role, db.session))

    with papp.app_context():
        Mause = db.session.query(User).filter_by(username='Mause').one_or_none()
        if Mause:
            Mause.roles = list(set(Mause.roles) | {Roles.Admin, Roles.Member})
            db.session.commit()

    if 'sqlite' in papp.config['SQLALCHEMY_DATABASE_URI']:

        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.execute('pragma foreign_keys=ON')

        engine = db.get_engine(papp, None)
        event.listen(engine, 'connect', _fk_pragma_on_connect)
        _fk_pragma_on_connect(engine, None)

    return papp


class SearchForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])


@app.route('/user/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')


def check_auth(*args, **kwargs):
    auth = request.authorization
    if not auth:
        return abort(401, www_authenticate='Basic')

    um = current_app.user_manager
    user = um.db_manager.find_user_by_username(auth['username'])
    if not user:
        raise ProcessingException('No such user', 403)

    logging.log(auth)
    if um.verify_password(auth['password'], user.password):
        raise ProcessingException(description='Invalid credentials', code=403)

    if Roles.Member not in user.roles:
        raise ProcessingException(description='Not a member', code=401)


@app.before_request
def before():
    if not request.path.startswith('/user'):
        return login_required(roles_required('Member')(lambda: None))()


@app.route('/search')
def select_item() -> str:
    def get_url(item: Dict) -> str:
        return url_for(
            '.select_movie_options' if item['Type'] == 'movie' else '.select_season',
            imdb_id=item['imdbID'],
        )

    query = request.args['query']

    results = search_themoviedb(query)

    form = SearchForm(query=query)

    return render_template(
        'select_item.html', results=results, query=query, get_url=get_url, form=form
    )


def query_args(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rargs = request.args
        return func(*args, **kwargs, **{arg: rargs.get(arg, None) for arg in args_spec})

    args_spec = inspect.getfullargspec(func).args
    return wrapper


@app.route('/select/<imdb_id>/season/<season>/episode/<episode>/options')
def select_tv_options(imdb_id: str, season: str, episode: str) -> str:
    info = get_tv_episodes(imdb_id, season)['episodes'][int(episode) - 1]

    tv = get_tv(imdb_id)

    return select_options(
        'series',
        get_tv_imdb_id(imdb_id),
        display_title=info['name'] + ' - ' + tv['name'],
        title=info['name'],
        search_string=f'S{int(season):02d}E{int(episode):02d}',
        season=season,
        episode=episode,
    )


def eventstream(func: Callable):
    def decorator(*args, **kwargs):
        return Response(
            chain(
                (f'data: {json.dumps(rset)}\n\n' for rset in func(*args, **kwargs)),
                ['data:\n\n'],
            ),
            mimetype="text/event-stream",
        )

    return decorator


@app.route('/select/<imdb_id>/options/stream')
@eventstream
def stream(imdb_id: str):
    return chain.from_iterable(
        get_rarbg_iter(
            current_app.config['TORRENT_API_URL'],
            'movie',
            search_imdb=get_movie_imdb_id(imdb_id),
        )
    )


@app.route('/select/<imdb_id>/options')
def select_movie_options(imdb_id: str) -> str:
    return select_options(
        'movie', get_movie_imdb_id(imdb_id), title=get_movie(imdb_id)['title']
    )


@app.route('/delete/<type>/<id>')
def delete(type: str, id: str) -> WResponse:
    query = db.session.query(
        EpisodeDetails if type == 'series' else MovieDetails
    ).filter_by(id=id)
    assert query.count() > 0
    query.delete()
    db.session.commit()

    return redirect(url_for('.index'))


def categorise(string: str) -> str:
    if string.startswith('Movies/'):
        return string[7:]
    elif string.startswith('Movs/'):
        return string[5:]
    else:
        return string


def select_options(
    type: str,
    imdb_id: str,
    title: str,
    display_title: str = None,
    search_string: str = None,
    **extra,
) -> str:
    def build_download_link(option):
        return url_for(
            '.download',
            type=type,
            magnet=option['download'],
            imdb_id=imdb_id,
            titles=[title],
            **extra,
        )

    def already_downloaded(result):
        t = get_keyed_torrents()
        url = urlparse(result['download'])
        hash_string = dict(parse_qsl(url.query))['xt'].split(':')[-1]

        return hash_string in t

    manual_link = url_for(
        '.manual', type=type, imdb_id=imdb_id, titles=[title], **extra
    )

    display_title = display_title or title

    query = {'search_string': search_string, 'search_imdb': imdb_id}
    print(query)
    results = get_rarbg(current_app.config['TORRENT_API_URL'], type, **query)

    with open('ranking.json') as fh:
        ranking = json.load(fh)

    categorized = list(
        groupby(results, lambda result: categorise(result['category'])).items()
    )
    categorized = sorted(
        categorized, key=lambda pair: ranking.index(pair[0]), reverse=True
    )
    ten_eighty = dict(categorized).get(
        'x264/1080' if type == 'movie' else 'TV HD Episodes', []
    )
    auto: Optional[RarbgTorrent] = None
    if ten_eighty:
        auto = max(ten_eighty, key=lambda torrent: torrent['seeders'])

    return render_template(
        'select_options.html',
        results=categorized,
        imdb_id=imdb_id,
        auto=auto,
        type=type,
        display_title=display_title,
        build_download_link=build_download_link,
        already_downloaded=already_downloaded,
        manual_link=manual_link,
    )


@app.route('/select/<imdb_id>/season/<season>')
def select_episode(imdb_id: str, season: str) -> str:
    def build_episode_link(episode: Dict) -> str:
        return url_for(
            '.select_tv_options',
            imdb_id=imdb_id,
            season=season,
            episode=episode["episode_number"],
        )

    return render_template(
        'select_episode.html',
        imdb_id=imdb_id,
        title=get_tv(imdb_id)['name'],
        season=season,
        episodes=get_tv_episodes(imdb_id, season)['episodes'],
        build_episode_link=build_episode_link,
    )


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

    print(title, sel.groups())

    episode = episodes[int(i_episode, 10) - 1]

    to_replace = punctuation_re.sub(' ', episode['name'])
    to_replace = '.'.join(to_replace.split())
    print('to_replace', to_replace)
    title = re.sub(to_replace, 'TITLE', title, re.I)

    title = title.replace(full, 'S00E00')

    return title


def extract_marker(title: str) -> Tuple[str, Optional[str]]:
    m = full_marker_re.search(title)
    if not m:
        m = partial_marker_re.search(title)
        assert m, title
        return m.group(2), None
    return cast(Tuple[str, str], tuple(m.groups()[1:]))


@app.route('/select/<imdb_id>/season/<season>/download_all')
def download_all_episodes(imdb_id: str, season: str) -> str:
    def build_download_link(imdb_id: str, season: str, result_set: List[Dict]) -> str:
        def get_title(title: str) -> str:
            _, i_episode = extract_marker(title)
            if i_episode is None:
                return f'Season {season}'
            return episodes[int(i_episode) - 1]['name']

        return url_for(
            '.download',
            type='series',
            imdb_id=imdb_id,
            season=season,
            titles=[get_title(r['title']) for r in result_set],
            magnet=[r['download'] for r in result_set],
        )

    results = get_rarbg(
        current_app.config['TORRENT_API_URL'],
        'series',
        search_imdb=get_tv_imdb_id(imdb_id),
        search_string=f'S{int(season):02d}',
    )

    episodes = get_tv_episodes(imdb_id, season)['episodes']

    packs_or_not = groupby(
        results, lambda result: extract_marker(result['title'])[1] is None
    )
    packs = sorted(
        packs_or_not.get(True, []), key=lambda result: result['seeders'], reverse=True
    )

    grouped_results = groupby(
        packs_or_not.get(False, []), lambda result: normalise(episodes, result['title'])
    )
    complete_or_not = groupby(
        grouped_results.items(), lambda rset: len(rset[1]) == len(episodes)
    )

    return render_template(
        'download_all.html',
        info=get_tv(imdb_id),
        season=season,
        imdb_id=get_tv_imdb_id(imdb_id),
        packs=packs,
        super_results=[
            ('Complete', complete_or_not.get(True, [])),
            ('Incomplete', complete_or_not.get(False, [])),
        ],
        build_download_link=build_download_link,
    )


@app.route('/select/<imdb_id>/season')
def select_season(imdb_id: str) -> str:
    info = get_tv(imdb_id)

    print(info)

    total_seasons = info['number_of_seasons']

    return render_template(
        'select_season.html', info=info, seasons=list(range(1, int(total_seasons) + 1))
    )


@app.route('/download/<type>')
def download(type: str) -> WResponse:
    assert type

    args = request.args

    imdb_id = args['imdb_id']

    season = args.get('season')
    episode = None

    titles: List[str] = args.getlist('titles')
    magnets: List[str] = args.getlist('magnet')

    is_tv = type == 'series'
    tv_id = resolve_id(imdb_id)
    item = get_tv(tv_id) if is_tv else get_movie(tv_id)

    if is_tv:
        subpath = f'tv_shows/{item["name"]}/Season {season}'
    else:
        subpath = 'movies'

    for title, magnet in zip_longest(titles, magnets):
        if is_tv:
            season, episode = extract_marker(magnet)
        add_single(
            magnet=magnet,
            subpath=subpath,
            imdb_id=imdb_id,
            episode=episode,
            season=season,
            is_tv=is_tv,
            title=title if is_tv else item['title'],
            show_title=item["name"] if is_tv else None,
        )

    return redirect(url_for('.index'))


class ManualForm(FlaskForm):
    magnet = StringField(
        'Magnet link', validators=[DataRequired(), Regexp(r'^magnet:')]
    )


@app.route('/manual', methods=['POST', 'GET'])
def manual():
    form = ManualForm()

    if form.validate_on_submit():
        return redirect(
            url_for('.download', **request.args, magnet=form.data['magnet'])
        )
    else:
        return render_template('manual.html', form=form)


def add_single(
    *,
    magnet: str,
    subpath: str,
    is_tv: bool,
    imdb_id: str,
    season: Optional[str],
    episode: Optional[str],
    title: str,
    show_title: Optional[str],
) -> None:
    arguments = torrent_add(magnet, subpath)['arguments']
    print(arguments)
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
            assert season
            create_episode(
                transmission_id, imdb_id, season, episode, title, show_title=show_title
            )
        else:
            create_movie(transmission_id, imdb_id, title=title)

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
    return [
        EpisodeDetails(
            id=-1,
            download=Download(
                id=-1,
                transmission_id=f'{pack.download.transmission_id}.{episode["episode_number"]}',
                title=episode['name'],
                imdb_id=pack.download.imdb_id,
                type='episode',
            ),
            season=pack.season,
            episode=episode['episode_number'],
            show_title=pack.show_title,
        )
        for episode in get_tv_episodes(resolve_id(pack.download.imdb_id), pack.season)[
            'episodes'
        ]
    ]


def resolve_show(
    imdb_id: str, show: List[EpisodeDetails]
) -> Dict[int, List[EpisodeDetails]]:
    seasons = groupby(show, lambda episode: episode.season)
    return {
        number: resolve_season(
            sorted(season, key=lambda episode: episode.episode or -1)
        )
        for number, season in seasons.items()
    }


class SeriesDetails(TypedDict):
    seasons: Dict[int, List[EpisodeDetails]]
    title: str
    imdb_id: str


def resolve_series() -> List[SeriesDetails]:
    episodes = get_episodes()

    return [
        {
            'title': show[0].show_title,
            'seasons': resolve_show(imdb_id, show),
            'imdb_id': imdb_id,
        }
        for imdb_id, show in groupby(
            episodes, lambda episode: episode.download.imdb_id
        ).items()
    ]


@app.route('/api/index')
@jsonapi
def api_index():
    return {'series': resolve_series(), 'movies': get_movies()}


@app.route('/api/torrents')
@jsonapi
def api_torrents():
    return get_keyed_torrents()


def render_progress(
    torrents: Dict[str, Dict], item: Union[MovieDetails, EpisodeDetails]
) -> str:
    DEFAULT = {'percentDone': 1, 'eta': 0}
    tid = item.download.transmission_id
    item_id = None
    if '.' in str(tid):
        tid, item_id = tid.split('.')
        if tid in torrents:
            key = item.get_marker().lower()
            files = torrents[tid]['files']
            torrent = next(f for f in files if key in f['name'].lower())
            torrent = {
                'eta': -1,
                'percentDone': (torrent['bytesCompleted'] / torrent['length']),
            }
        else:
            torrent = DEFAULT
    else:
        torrent = torrents.get(tid, DEFAULT)
    pc = torrent['percentDone']
    eta = naturaldelta(torrent['eta']) if torrent['eta'] > 0 else 'Unknown time'

    if pc == 1:
        return '<i class="fas fa-check-circle"></i>'
    else:
        return f'''
        <progress value="{pc}" title="{pc * 100:.02f}% ({eta} remaining)">
        </progress>
        '''


@app.route('/test/<tmdb_id>')
def test(tmdb_id: str) -> str:
    init = {
        'imdb_id': get_movie_imdb_id(tmdb_id),
        'title': get_movie(tmdb_id)['title'],
        'tmdb_id': tmdb_id,
    }

    return render_template('test.html', init=json.dumps(init), e=e, title=init['title'])


@app.route('/', methods=['GET', 'POST'])
def index() -> Union[str, WResponse]:
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('.select_item', query=form.data['query']))

    series = resolve_series()
    torrents = get_keyed_torrents()

    return render_template(
        'index.html',
        form=form,
        # data
        movies=get_movies(),
        series=series,
        torrents=torrents,
        # functions
        sorted=sorted,
        render_progress=render_progress,
        resolve_id=resolve_id,
    )


def get_keyed_torrents() -> Dict[str, Dict]:
    if hasattr(g, 'get_keyed_torrents'):
        return g.get_keyed_torrents
    else:
        g.get_keyed_torrents = _get_keyed_torrents()
        return g.get_keyed_torrents


def _get_keyed_torrents() -> Dict[str, Dict]:
    try:
        return {t['hashString']: t for t in get_torrent()['arguments']['torrents']}
    except (
        ConnectionError,
        ConnectionRefusedError,
        TimeoutError,
        FutureTimeoutError,
    ) as e:
        error = 'Unable to connect to transmission'
        return abort(
            500,
            error,
            Response(
                f'''
                <h3>{error}</h3>
                <code>{repr(e)}</code>
                ''',
                500,
            ),
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


@app.route('/endpoints.json')
def endpoints() -> Response:
    return jsonify([r.rule for r in current_app.url_map._rules])


if __name__ == '__main__':
    create_app({}).run(debug=True, host='0.0.0.0')
