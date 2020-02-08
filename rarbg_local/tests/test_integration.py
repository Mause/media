from typing import Generator
from unittest.mock import MagicMock, Mock, patch

from flask import Flask, Request
from flask.globals import _request_ctx_stack
from flask.testing import FlaskClient
from flask_login import login_user
from lxml.html import fromstring
from pytest import fixture, mark, raises
from responses import RequestsMock
from sqlalchemy.exc import IntegrityError

from ..db import Download, Role, Roles, User, create_episode, db
from ..main import create_app
from ..utils import cache_clear
from .conftest import add_json, themoviedb

HASH_STRING = '00000000000000000'


@fixture
def clear_cache():
    cache_clear()


@fixture
def flask_app() -> Flask:
    return create_app(
        {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'ENV': 'development',
            'TESTING': True,
        }
    )


@fixture(scope='function')
def responses():
    mock = RequestsMock()
    try:
        mock.start()
        yield mock

    finally:
        mock.stop()


@fixture
def test_client(clear_cache, flask_app: Flask) -> Generator[FlaskClient, None, None]:
    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

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
    with patch('rarbg_local.main.torrent_add', return_value=res):
        yield


@fixture
def user():
    u = User(username='python', password='is-great!')
    u.roles = [Role(name='Member')]
    db.session.add(u)
    db.session.commit()
    return u


@fixture
def logged_in(flask_app, test_client, user):
    with patch.object(flask_app.login_manager, 'request_callback', return_value=user):
        with flask_app.app_context():
            rq: Request = Mock(spec=Request, headers={}, remote_addr='', environ={})

            _request_ctx_stack.push(MagicMock(session={}, request=rq))
            login_user(user)

            yield

            _request_ctx_stack.pop()


def test_download(test_client, logged_in, responses, add_torrent):
    themoviedb(responses, '/tv/95792', {'name': 'Pocket Monsters'})
    themoviedb(responses, '/tv/95792/external_ids', {'imdb_id': 'ttwhatever'})
    themoviedb(
        responses,
        '/tv/95792/season/1',
        {'episodes': [None, {'name': "Satoshi, Go, and Lugia Go!"}]},
    )

    res = test_client.post(
        '/api/download',
        json=[
            {
                'magnet': 'magnet:?xt=urn:btih:dacf233f2586b49709fd3526b390033849438313&dn=%5BSome-Stuffs%5D_Pocket_Monsters_%282019%29_002_%281080p%29_%5BCCBE335E%5D.mkv&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce',
                'tmdb_id': '95792',
                'season': '1',
                'episode': '2',
            }
        ],
    )
    assert res.status == '200 OK'

    download = db.session.query(Download).first()
    assert download
    assert download.episode


@mark.skip
def test_index(responses, test_client, flask_app, get_torrent, logged_in):
    create_episode(
        transmission_id=HASH_STRING,
        imdb_id='tt000000',
        season='1',
        tmdb_id=1,
        episode='1',
        title='Hello world',
        show_title='Programming',
    )
    db.session.commit()

    themoviedb(
        responses,
        '/find/tt000000',
        {'tv_results': [{'id': 1}]},
        query='&external_source=imdb_id',
    )

    res = test_client.get('/old')

    assert res.status == '200 OK'

    lists = fromstring(res.get_data()).xpath('.//li/span/text()')
    lists = [t.strip() for t in lists]

    assert ''.join(lists) == 'Hello world'


@mark.skip
def test_search(responses, test_client, logged_in):
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

    res = test_client.get('/search?query=chernobyl')
    assert res.status == '200 OK'

    html = fromstring(res.get_data()).xpath('.//li/a/text()')
    html = [t.strip() for t in html]

    assert html == ['Chernobyl (2019)']


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
