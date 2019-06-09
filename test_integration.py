import json

import responses
from pytest import fixture
from lxml.html import fromstring
from flask import Flask

from main import create_app
from db import create_episode, db
from tmdb import cache_clear


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


@fixture
def test_client(clear_cache, flask_app):
    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    with flask_app.app_context():
        yield testing_client  # this is where the testing happens!


@fixture
def trm_session():
    responses.add(
        method='POST',
        url='http://novell.local:9091/transmission/rpc',
        headers={'X-Transmission-Session-Id': 'XXXXXXX'},
    )


def add_json(method: str, url: str, json_body) -> None:
    responses.add(method=method, url=url, body=json.dumps(json_body))


@fixture
def reverse_imdb():
    themoviedb(
        '/find/tt000000',
        {'tv_results': [{'id': '100000'}]},
        '&external_source=imdb_id',
    )
    themoviedb('/tv/100000', {'name': 'Introductory'})


@responses.activate
def test_index(test_client, trm_session, reverse_imdb):
    add_json(
        'POST',
        'http://novell.local:9091/transmission/rpc',
        {
            'arguments': {
                'torrents': [{'id': 1, 'eta': 10000, 'percentDone': 0.5}]
            }
        },
    )

    create_episode(
        transmission_id=1,
        imdb_id='tt000000',
        season=1,
        episode=1,
        title='Hello world',
    )
    db.session.commit()

    res = test_client.get('/')

    assert res.status == '200 OK'

    lists = fromstring(res.get_data()).xpath('.//li/text()')
    lists = [t.strip() for t in lists]

    assert ''.join(lists) == 'Hello world'


@responses.activate
def test_search(test_client):
    themoviedb(
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


def themoviedb(path, response, query=''):
    add_json(
        'GET',
        f'https://api.themoviedb.org/3{path}?api_key=66b197263af60702ba14852b4ec9b143'
        + query,
        response,
    )
