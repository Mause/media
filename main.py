import re
import json
import string
import inspect
import logging
from typing import (
    Dict,
    List,
    Optional,
    Union,
    Iterable,
    Callable,
    TypeVar,
    Tuple,
    cast,
)
from collections import defaultdict
from functools import wraps
from itertools import zip_longest

from flask_wtf import FlaskForm
from wtforms import StringField
from humanize import naturaldelta
from wtforms.validators import DataRequired
from sqlalchemy import event
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    Response,
    Blueprint,
    current_app,
)
from werkzeug.wrappers import Response as WResponse
from requests.exceptions import ConnectionError

from rarbg import get_rarbg
from transmission import torrent_add, get_torrent
from db import (
    create_movie,
    get_movies,
    get_episodes,
    create_episode,
    EpisodeDetails,
    MovieDetails,
    Download,
    db,
)
from tmdb import (
    search_themoviedb,
    get_tv,
    resolve_id,
    get_tv_episodes,
    get_movie,
    get_tv_imdb_id,
    get_movie_imdb_id,
)

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
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.db',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'TRANSMISSION_URL': 'http://novell.local:9091/transmission/rpc',
            **config,
        }
    )
    db.init_app(papp)
    db.create_all(app=papp)

    if 'sqlite' in papp.config['SQLALCHEMY_DATABASE_URI']:
        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.execute('pragma foreign_keys=ON')

        engine = db.get_engine(papp, None)
        event.listen(engine, 'connect', _fk_pragma_on_connect)
        _fk_pragma_on_connect(engine, None)

    return papp


class SearchForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])


@app.route('/search/<query>')
def select_item(query: str) -> Response:
    results = search_themoviedb(query)

    return render_template('select_item.html', results=results, query=query)


def query_args(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rargs = request.args
        return func(
            *args, **kwargs, **{arg: rargs.get(arg, None) for arg in args_spec}
        )

    args_spec = inspect.getfullargspec(func).args
    return wrapper


@app.route('/select/<imdb_id>/season/<season>/episode/<episode>/options')
def select_tv_options(imdb_id: str, season: str, episode: str) -> Response:
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


@app.route('/select/<imdb_id>/options')
def select_movie_options(imdb_id: str) -> Response:
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
) -> Response:
    def build_download_link(option):
        return url_for(
            '.download',
            type=type,
            magnet=option['download'],
            imdb_id=imdb_id,
            titles=[title],
            **extra,
        )
    display_title = display_title or title

    query = {'search_string': search_string, 'search_imdb': imdb_id}
    print(query)
    results = get_rarbg(type, **query)

    with open('ranking.json') as fh:
        ranking = json.load(fh)

    results = groupby(results, lambda result: categorise(result['category']))
    results = sorted(
        results.items(), key=lambda pair: ranking.index(pair[0]), reverse=True
    )

    return render_template(
        'select_options.html',
        results=results,
        imdb_id=imdb_id,
        display_title=display_title,
        build_download_link=build_download_link,
    )


@app.route('/select/<imdb_id>/season/<season>')
def select_episode(imdb_id: str, season: str) -> Response:
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
def download_all_episodes(imdb_id: str, season: str) -> WResponse:
    def build_download_link(
        imdb_id: str, season: str, result_set: List[Dict]
    ) -> str:
        def get_title(title: str) -> str:
            try:
                _, i_episode = extract_marker(title)
            except AssertionError:
                return title
            assert i_episode, title
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
        'series',
        search_imdb=get_tv_imdb_id(imdb_id),
        search_string=f'S{int(season):02d}',
    )

    episodes = get_tv_episodes(imdb_id, season)['episodes']

    results = groupby(
        results, lambda result: normalise(episodes, result['title'])
    )

    return render_template(
        'download_all.html',
        info=get_tv(imdb_id),
        season=season,
        imdb_id=get_tv_imdb_id(imdb_id),
        results=results,
        build_download_link=build_download_link,
    )


@app.route('/select/<imdb_id>/season')
def select_season(imdb_id: str) -> Response:
    info = get_tv(imdb_id)

    print(info)

    total_seasons = info['number_of_seasons']

    return render_template(
        'select_season.html',
        info=info,
        seasons=list(range(1, int(total_seasons) + 1)),
    )


@app.route('/download/<type>')
def download(type: str) -> WResponse:
    assert type

    args = request.args

    imdb_id = args['imdb_id']

    season = args.get('season')

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


def add_single(
    *,
    magnet: str,
    subpath: str,
    is_tv: bool,
    imdb_id: str,
    season: Optional[str],
    episode: Optional[str],
    title: str,
    show_title: str,
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
                transmission_id,
                imdb_id,
                season,
                episode,
                title,
                show_title=show_title,
            )
        else:
            create_movie(transmission_id, imdb_id, title=title)

        db.session.commit()


def groupby(iterable: Iterable[V], key: Callable[[V], K]) -> Dict[K, List[V]]:
    dd: Dict[K, List[V]] = defaultdict(list)
    for item in iterable:
        dd[key(item)].append(item)
    return dict(dd)


def resolve_show(
    imdb_id: str, show: List[EpisodeDetails]
) -> Dict[int, List[EpisodeDetails]]:
    seasons = groupby(show, lambda episode: episode.season)
    return {
        number: sorted(season, key=lambda episode: episode.episode or -1)
        for number, season in seasons.items()
    }


def resolve_series() -> Dict[str, Dict[int, List[EpisodeDetails]]]:
    episodes = get_episodes()

    return {
        show[0].show_title: resolve_show(imdb_id, show)
        for imdb_id, show in groupby(
            episodes, lambda episode: episode.download.imdb_id
        ).items()
    }


def render_progress(
    torrents: Dict[str, Dict], item: Union[MovieDetails, EpisodeDetails]
) -> str:
    torrent = torrents.get(
        item.download.transmission_id, {'percentDone': 1, 'eta': 0}
    )
    pc = torrent['percentDone']
    eta = naturaldelta(torrent['eta']) if torrent['eta'] > 0 else 'Unknown time'

    if pc == 1:
        return '<i class="fas fa-check-circle"></i>'
    else:
        return f'''
        <progress value="{pc}" title="{pc * 100:.02f}% ({eta} remaining)">
        </progress>
        '''


@app.route('/', methods=['GET', 'POST'])
def index() -> WResponse:
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
    )


def get_keyed_torrents() -> Dict[str, Dict]:
    try:
        return {
            t['hashString']: t for t in get_torrent()['arguments']['torrents']
        }
    except (ConnectionError, ConnectionRefusedError) as e:
        url = current_app.config["TRANSMISSION_URL"]
        error = 'Unable to connect to transmission'
        return abort(
            500,
            error,
            Response(
                f'''
                <h3 class="error">{error}: {url}</h3>
                <code>{repr(e)}</code>
                ''',
                500,
            )
        )


@app.route('/redirect/<type_>/<ident>')
def redirect_to_imdb(type_: str, ident: str):
    imdb_id = (
        get_movie_imdb_id(ident) if type_ == 'movie' else get_tv_imdb_id(ident)
    )

    return redirect(f'https://www.imdb.com/title/{imdb_id}')


@app.route('/endpoints.json')
def endpoints() -> Response:
    return jsonify([r.rule for r in app.url_map._rules])


if __name__ == '__main__':
    create_app({}).run(debug=True, host='0.0.0.0')
