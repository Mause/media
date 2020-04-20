from base64 import b64encode
from datetime import datetime
from typing import Dict, Generator
from unittest.mock import MagicMock, Mock, patch

from flask import Flask, Request
from flask.globals import _request_ctx_stack
from flask.testing import FlaskClient
from flask_login import FlaskLoginClient, login_user
from flask_restx.swagger import Swagger
from pytest import fixture, mark, raises
from responses import RequestsMock
from sqlalchemy.exc import IntegrityError

from ..db import Download, Role, User, create_episode, db
from ..main import api, create_app
from ..utils import cache_clear
from .conftest import themoviedb

HASH_STRING = '00000000000000000'


@fixture
def clear_cache():
    cache_clear()


@fixture
def flask_app() -> Generator[Flask, None, None]:
    app = create_app(
        {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_ECHO': False,
            'ENV': 'development',
            'TESTING': True,
        }
    )

    app.test_client_class = FlaskLoginClient

    with app.app_context():
        yield app


@fixture
def test_client(
    clear_cache, flask_app: Flask, user: User
) -> Generator[FlaskClient, None, None]:
    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client(user=user)

    # Establish an application context before running the tests.
    with flask_app.app_context():
        yield testing_client  # this is where the testing happens!


@fixture
def get_torrent():
    res = {
        'arguments': {
            'torrents': [
                {'id': 1, 'eta': 10000, 'percentDone': 0.5, 'hashString': HASH_STRING}
            ]
        }
    }
    with patch('rarbg_local.main.get_torrent', return_value=res):
        yield


@fixture
def add_torrent():
    res = {'arguments': {'torrent-added': {'hashString': HASH_STRING}}}
    with patch('rarbg_local.main.torrent_add', return_value=res) as mock:
        yield mock


@fixture
def user(flask_app):
    u = User(
        username='python', password=flask_app.user_manager.hash_password('is-great!')
    )
    u.roles = [Role(name='Member')]
    db.session.add(u)
    db.session.commit()
    return u


@fixture
def logged_in(flask_app, test_client, user):
    with patch.object(flask_app.login_manager, '_request_callback', return_value=user):
        with flask_app.app_context():
            rq: Request = Mock(spec=Request, headers={}, remote_addr='', environ={})

            _request_ctx_stack.push(MagicMock(session={}, request=rq))
            login_user(user)

            yield

            _request_ctx_stack.pop()


def test_basic_auth(flask_app, user):
    with flask_app.test_client() as client:
        r = client.get(
            '/diagnostics',
            headers={
                'Authorization': 'Basic ' + b64encode(b'python:is-great!').decode()
            },
        )
        assert r.status_code == 200
        assert r.json == {}


def test_download_movie(test_client, responses, add_torrent):
    themoviedb(responses, '/movie/533985', {'title': 'Bit'})
    themoviedb(responses, '/movie/533985/external_ids', {'imdb_id': "tt8425034"})

    magnet = 'magnet:...'

    res = test_client.post(
        '/api/download', json=[{'magnet': magnet, 'tmdb_id': 533985}]
    )
    assert res.status == '200 OK'

    add_torrent.assert_called_with(magnet, 'movies')

    download = db.session.query(Download).first()
    assert download.title == 'Bit'


def test_download(test_client, responses, add_torrent):
    themoviedb(responses, '/tv/95792', {'name': 'Pocket Monsters'})
    themoviedb(responses, '/tv/95792/external_ids', {'imdb_id': 'ttwhatever'})
    themoviedb(
        responses,
        '/tv/95792/season/1',
        {'episodes': [None, {'name': "Satoshi, Go, and Lugia Go!"}]},
    )

    magnet = 'magnet:?xt=urn:btih:dacf233f2586b49709fd3526b390033849438313&dn=%5BSome-Stuffs%5D_Pocket_Monsters_%282019%29_002_%281080p%29_%5BCCBE335E%5D.mkv&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce'

    res = test_client.post(
        '/api/download',
        json=[{'magnet': magnet, 'tmdb_id': 95792, 'season': '1', 'episode': '2'}],
    )
    assert res.status == '200 OK'

    add_torrent.assert_called_with(magnet, 'tv_shows/Pocket Monsters/Season 1')

    download = db.session.query(Download).first()
    assert download
    assert download.title == 'Satoshi, Go, and Lugia Go!'
    assert download.episode
    assert download.episode.season == 1
    assert download.episode.episode == 2
    assert download.episode.show_title == 'Pocket Monsters'


def test_download_season_pack(test_client, responses, add_torrent):
    themoviedb(responses, '/tv/90000', {'name': 'Watchmen'})
    themoviedb(responses, '/tv/90000/external_ids', {'imdb_id': 'ttwhatever'})

    magnet = 'magnet:?xt=urn:btih:dacf233f2586b49709fd3526b390033849438313&dn=%5BSome-Stuffs%5D_Pocket_Monsters_%282019%29_002_%281080p%29_%5BCCBE335E%5D.mkv&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce'

    res = test_client.post(
        '/api/download', json=[{'magnet': magnet, 'tmdb_id': 90000, 'season': '1'}]
    )
    assert res.status == '200 OK'

    add_torrent.assert_called_with(magnet, 'tv_shows/Watchmen/Season 1')

    download = db.session.query(Download).first()
    assert download
    assert download.title == 'Season 1'
    assert download.episode
    assert download.episode.season == 1
    assert download.episode.episode is None
    assert download.episode.show_title == 'Watchmen'


def shallow(d: Dict):
    return {k: v for k, v in d.items() if not isinstance(v, dict)}


def test_index(responses, test_client, flask_app, get_torrent, logged_in):
    create_episode(
        transmission_id=HASH_STRING,
        imdb_id='tt000000',
        season='1',
        tmdb_id=1,
        episode='1',
        title='Hello world',
        show_title='Programming',
        timestamp=datetime(2020, 4, 21),
    )
    db.session.commit()

    res = test_client.get('/api/index')

    assert res.status == '200 OK'

    js = res.json

    assert set(js.keys()) == {'movies', 'series'}
    assert js['movies'] == []
    assert len(js['series']) == 1

    series = js['series'][0]

    assert shallow(series) == {
        'imdb_id': 'tt000000',
        'title': 'Programming',
        'tmdb_id': 1,
    }
    (episode,) = series['seasons']['1']
    assert shallow(episode) == {
        'show_title': 'Programming',
        'episode': 1,
        'season': 1,
        'id': 1,
    }
    assert shallow(episode['download']) == {
        'tmdb_id': 1,
        'transmission_id': HASH_STRING,
        'added_by_id': 1,
        'imdb_id': 'tt000000',
        'movie_id': None,
        'timestamp': 'Tue, 21 Apr 2020 00:00:00 GMT',
        'episode_id': 1,
        'id': 1,
        'type': 'episode',
        'title': 'Hello world',
    }
    assert shallow(episode['download']['added_by']) == {
        'active': True,
        'first_name': '',
        'id': 1,
        'last_name': '',
        'username': 'python',
    }


def test_search(responses, test_client):
    themoviedb(
        responses,
        '/search/multi',
        {
            'results': [
                {
                    'id': '10000',
                    'media_type': 'tv',
                    'name': 'Chernobyl',
                    'first_air_date': '2019-01-01',
                }
            ]
        },
        query='&query=chernobyl',
    )

    res = test_client.get('/api/search?query=chernobyl')
    assert res.status == '200 OK'
    assert res.json == [
        {'Type': 'series', 'imdbID': 10000, 'title': 'Chernobyl', 'Year': 2019}
    ]


def test_delete_cascade(test_client: FlaskClient, logged_in):
    from ..main import db, get_episodes, Download

    e = create_episode(
        transmission_id='1',
        imdb_id='tt000000',
        tmdb_id=1,
        season='1',
        episode='1',
        title='Title',
        show_title='',
    )

    session = db.session

    session.commit()

    assert len(get_episodes()) == 1
    assert len(session.query(Download).all()) == 1

    res = test_client.get(f'/delete/series/{e.id}')
    assert res.status_code == 200
    assert res.data == b'{}\n'

    session.commit()

    assert len(get_episodes()) == 0
    assert len(session.query(Download).all()) == 0


@mark.skip
def test_select_season(
    responses: RequestsMock, test_client: FlaskClient, logged_in
) -> None:
    themoviedb(responses, '/tv/100000', {'number_of_seasons': 1})

    res = test_client.get('/select/100000/season')

    assert res.status == '200 OK'

    assert res.get_data()


def test_foreign_key_integrity(flask_app: Flask):
    from ..main import db, Download

    with flask_app.app_context():
        session = db.session

        # invalid fkey_id
        ins = Download.__table__.insert().values(id=1, movie_id=99)
        with raises(IntegrityError):
            session.execute(ins)


def test_delete_monitor(responses, test_client):
    themoviedb(responses, '/movie/5', {'title': 'Hello World'})
    ls = test_client.get('/api/monitor').json
    assert ls == []

    r = test_client.post('/api/monitor', json={'tmdb_id': 5, 'type': 'MOVIE'})
    assert r.status == '201 CREATED'

    ls = test_client.get('/api/monitor').json

    assert ls == [
        {
            'type': 'MOVIE',
            'title': 'Hello World',
            'tmdb_id': 5,
            'id': 1,
            'added_by': 'python',
        }
    ]
    ident = ls[0]['id']

    r = test_client.delete(f'/api/monitor/{ident}')
    assert r.status == '200 OK'

    ls = test_client.get('/api/monitor').json
    assert ls == []


def test_stats(test_client):
    test_client.get('/api/stats')


@patch('rarbg_local.main.get_torrent')
def test_torrents_error(get_torrent, test_client):
    get_torrent.side_effect = TimeoutError('Timeout!')
    torrents = test_client.get('/api/torrents')
    assert torrents.status_code == 500
    assert torrents.json == {'message': 'Unable to connect to transmission: Timeout!'}


@patch('rarbg_local.main.get_torrent')
def test_torrents(get_torrent, test_client):
    get_torrent.return_value = {
        'arguments': {'torrents': [{'hashString': '00000', 'filename': 'movie.mov'}]}
    }
    torrents = test_client.get('/api/torrents')
    assert torrents.json == {'00000': {'hashString': '00000', 'filename': 'movie.mov'}}


@mark.skip
def test_manifest(test_client):
    r = test_client.get('/manifest.json')

    assert 'name' in r.json


def test_swagger(flask_app, snapshot):
    with flask_app.test_request_context():
        swagger = Swagger(api).as_dict()
        snapshot.assert_match(swagger)
