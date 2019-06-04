import json
from main import create_app
from pytest import fixture
import responses
from db import create_episode, db


@fixture(scope='module')
def test_client():
    flask_app = create_app(
        {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'ENV': 'development',
            'TESTING': True,
        }
    )

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


@fixture
def reverse_imdb():
    responses.add(
        method='GET',
        url='https://api.themoviedb.org/3/find/tt000000?'
        'api_key=66b197263af60702ba14852b4ec9b143&external_source=imdb_id',
        body=json.dumps({'tv_results': [{'id': '100000'}]}),
    )
    responses.add(
        method='GET',
        url='https://api.themoviedb.org/3/tv/100000?api_key=66b197263af60702ba14852b4ec9b143',
        body=json.dumps({'name': 'Introductory'}),
    )


@responses.activate
def test_index(test_client, trm_session, reverse_imdb):
    responses.add(
        method='POST',
        url='http://novell.local:9091/transmission/rpc',
        body=json.dumps(
            {
                'arguments': {
                    'torrents': [{'id': 1, 'eta': 10000, 'percentDone': 0.5}]
                }
            }
        ),
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
    assert b'Hello world' in res.get_data()


def test_search(test_client):
    assert test_client.get('/search/chernobyl').status == '200 OK'
