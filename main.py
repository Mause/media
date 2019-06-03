import re
import json
import string
import inspect
import logging
from typing import Dict, List, Optional, Union, Iterable, Callable, TypeVar
from collections import defaultdict
from functools import wraps

from flask_wtf import FlaskForm
from wtforms import StringField
from humanize import naturaldelta
from wtforms.validators import DataRequired
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    render_template_string,
    jsonify,
    Response,
    Blueprint,
)
from werkzeug.wrappers import Response as WResponse

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
            **config,
        }
    )
    db.init_app(papp)
    db.create_all(app=papp)

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
        info['name'] + ' - ' + tv['name'],
        search_string=f'S{int(season):02d}E{int(episode):02d}',
        season=season,
        episode=episode,
    )


@app.route('/select/<imdb_id>/options')
def select_movie_options(imdb_id: str) -> Response:
    return select_options(
        'movie', get_movie_imdb_id(imdb_id), title=get_movie(imdb_id)['title']
    )


@app.route('/delete')
@query_args
def delete(download_id: str) -> WResponse:
    query = db.session.query(Download).filter_by(id=download_id)
    print(query)
    query.delete()
    db.session.commit()

    return redirect(url_for('.index'))


def categorise(string: str) -> str:
    return string[7:] if string.startswith('Movies/') else string


def select_options(
    type: str, imdb_id: str, title: str, search_string: str = None, **extra
) -> Response:
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
        title=title,
        extra=dict(extra, title=title),
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


marker_re = re.compile(r'(S(\d{2})E(\d{2}))')
season_re = re.compile(r'\W(S\d{2})\W')
punctuation_re = re.compile(f'[{string.punctuation} ]')


def normalise(episodes: List[Dict], title: str) -> Optional[str]:
    sel = marker_re.search(title)
    if not sel:
        sel = season_re.search(title)
        if sel:
            return title

        print('unable to find marker in', title)
        return None

    full, _, i_episode = sel.groups()

    print(title, sel.groups())

    episode = episodes[int(i_episode, 10) - 1]

    to_replace = punctuation_re.sub('.', episode['name'])
    print('to_replace', to_replace)
    title = re.sub(to_replace, 'TITLE', title, re.I)

    title = title.replace(full, 'S00E00')

    return title


@app.route('/select/<imdb_id>/season/<season>/download_all')
def download_all_episodes(imdb_id: str, season: str) -> WResponse:
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


@app.route('/download')
@query_args
def download(
    magnet: str, imdb_id: str, season: str, episode: str, title: str
) -> WResponse:
    is_tv = bool(season)
    tv_id = resolve_id(imdb_id)
    item = get_tv(tv_id) if is_tv else get_movie(tv_id)

    if is_tv:
        subpath = f'tv_shows/{item["name"]}/Season {season}'
    else:
        subpath = 'movies'

    arguments = torrent_add(magnet, subpath)['arguments']
    print(arguments)
    transmission_id = (
        arguments['torrent-added']
        if 'torrent-added' in arguments
        else arguments['torrent-duplicate']
    )['id']

    already = (
        db.session.query(Download)
        .filter_by(transmission_id=transmission_id)
        .one_or_none()
    )

    print('already', already)
    if not already:
        if is_tv:
            create_episode(
                transmission_id, imdb_id, season, episode, title
            )
        else:
            create_movie(transmission_id, imdb_id, title=item['title'])

        db.session.commit()

    return redirect(url_for('.index'))


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
        get_tv(resolve_id(imdb_id))['name']: resolve_show(imdb_id, show)
        for imdb_id, show in groupby(
            episodes, lambda episode: episode.download.imdb_id
        ).items()
    }


def render_progress(
    torrents: Dict[str, Dict], item: Union[MovieDetails, EpisodeDetails]
) -> str:
    torrent = torrents[item.download.transmission_id]
    return render_template_string(
        '''
        {% if pc == 1 %}
            <i class="fas fa-check-circle"></i>
        {% else %}
            <progress value="{{ pc }}" title="{{ '{:.02f}'.format(pc * 100) }}% ({{eta}} remaining)"></progress>
        {% endif %}
        ''',
        pc=torrent['percentDone'],
        eta=naturaldelta(torrent['eta'])
        if torrent['eta'] > 0
        else 'Unknown time',
    )


@app.route('/', methods=['GET', 'POST'])
def index() -> WResponse:
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('.select_item', query=form.data['query']))

    torrents = {t['id']: t for t in get_torrent()['arguments']['torrents']}
    series = resolve_series()

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


@app.route('/endpoints.json')
def endpoints() -> Response:
    return jsonify([r.rule for r in app.url_map._rules])


if __name__ == '__main__':
    create_app({}).run(debug=True, host='0.0.0.0')
