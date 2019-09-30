import json
from typing import Generator

from flask import Flask
from flask.testing import FlaskClient
from lxml.html import fromstring
from pytest import fixture, raises
from responses import RequestsMock
from sqlalchemy.exc import IntegrityError

from db import create_episode, db
from main import create_app
from utils import cache_clear

transmission_url = 'http://novell.local:9091/transmission/rpc'
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
            'TRANSMISSION_URL': transmission_url,
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
def trm_session(responses):
    responses.add(
        method='POST',
        url=transmission_url,
        headers={'X-Transmission-Session-Id': 'XXXXXXX'},
    )


def add_json(responses, method: str, url: str, json_body) -> None:
    responses.add(method=method, url=url, body=json.dumps(json_body))


@fixture
def reverse_imdb(responses):
    themoviedb(
        responses,
        '/find/tt000000',
        {'tv_results': [{'id': '100000'}]},
        '&external_source=imdb_id',
    )
    themoviedb(
        responses, '/tv/100000', {'name': 'Introductory', 'number_of_seasons': 1}
    )


@fixture
def torrent_get(responses):
    add_json(
        responses,
        'POST',
        transmission_url,
        {
            'arguments': {
                'torrents': [
                    {
                        'id': 1,
                        'eta': 10000,
                        'percentDone': 0.5,
                        'hashString': HASH_STRING,
                    }
                ]
            }
        },
    )


def test_index(responses, test_client, trm_session, torrent_get):
    create_episode(
        transmission_id=HASH_STRING,
        imdb_id='tt000000',
        season=1,
        episode=1,
        title='Hello world',
        show_title='Programming',
    )
    db.session.commit()

    res = test_client.get('/')

    assert res.status == '200 OK'

    lists = fromstring(res.get_data()).xpath('.//li/span/text()')
    lists = [t.strip() for t in lists]

    assert ''.join(lists) == 'Hello world'


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

    res = test_client.get('/search/chernobyl')
    assert res.status == '200 OK'

    html = fromstring(res.get_data()).xpath('.//li/a/text()')
    html = [t.strip() for t in html]

    assert html == ['Chernobyl (2019)']


def themoviedb(responses, path, response, query=''):
    add_json(
        responses,
        'GET',
        f'https://api.themoviedb.org/3{path}?api_key=66b197263af60702ba14852b4ec9b143'
        + query,
        response,
    )


def test_delete_cascade(test_client: FlaskClient):
    from main import db, get_episodes, Download

    e = create_episode(1, 'tt000000', '1', '1', 'Title')

    session = db.session

    session.commit()

    assert len(get_episodes()) == 1
    assert len(session.query(Download).all()) == 1

    res = test_client.get(f'/delete/series/{e.id}')
    assert res.status_code == 302

    session.commit()

    assert len(get_episodes()) == 0
    assert len(session.query(Download).all()) == 0


def test_select_season(responses: RequestsMock, test_client: FlaskClient) -> None:
    themoviedb(responses, '/tv/100000', {'number_of_seasons': 1})

    res = test_client.get('/select/100000/season')

    assert res.status == '200 OK'

    assert res.get_data()


def test_foreign_key_integrity(flask_app: Flask):
    from main import db, Download

    with flask_app.app_context():
        session = db.session

        # invalid fkey_id
        ins = Download.__table__.insert().values(id=1, movie_id=99)
        with raises(IntegrityError):
            session.execute(ins)
