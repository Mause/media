import json
import logging
from datetime import datetime
from typing import Dict
from unittest.mock import patch

from async_asgi_testclient import TestClient
from pytest import fixture, mark, raises
from responses import RequestsMock
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from ..db import Download, create_episode, create_movie
from ..main import get_episodes
from ..new import SearchResponse
from .conftest import add_json, themoviedb
from .factories import (
    EpisodeDetailsFactory,
    MovieDetailsFactory,
    MovieResponseFactory,
    TvApiResponseFactory,
    UserFactory,
)

HASH_STRING = '00000000000000000'

logging.getLogger('faker.factory').disabled = True


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


@patch('rarbg_local.health.transmission')
@mark.asyncio
async def test_diagnostics(transmission, test_client, user, responses):
    responses.add('HEAD', 'https://horriblesubs.info')
    responses.add('HEAD', 'https://torrentapi.org')
    responses.add('HEAD', 'https://katcr.co')
    responses.add('GET', 'https://api.jikan.moe/v3', body='{}')

    transmission.return_value.channel.consumer_tags = ['ctag1']
    transmission.return_value._thread.is_alive.return_value = True

    r = await test_client.get('/api/diagnostics',)
    assert r.status_code == 200

    results = r.json()
    for r in results:
        r.pop('response_time')
        r.pop('timestamp')
        r.pop('expires')

    assert results == [
        {
            'checker': 'transmission_connectivity',
            'output': {'consumers': ['ctag1'], 'client_is_alive': True},
            'passed': True,
        },
        {'checker': 'jikan', 'output': {}, 'passed': True},
        {'checker': 'katcr', 'output': 'kickass', 'passed': True},
        {'checker': 'rarbg', 'output': 'rarbg', 'passed': True},
        {'checker': 'horriblesubs', 'output': 'horriblesubs', 'passed': True},
    ]


@mark.asyncio
async def test_download_movie(test_client, responses, add_torrent, session):
    themoviedb(
        responses, '/movie/533985', MovieResponseFactory.build(title='Bit').dict()
    )
    themoviedb(responses, '/movie/533985/external_ids', {'imdb_id': "tt8425034"})

    magnet = 'magnet:...'

    res = await test_client.post(
        '/api/download', json=[{'magnet': magnet, 'tmdb_id': 533985}]
    )
    assert res.status_code == 200

    add_torrent.assert_called_with(magnet, 'movies')

    download = session.query(Download).first()
    assert download.title == 'Bit'


@mark.asyncio
async def test_download(test_client, responses, add_torrent, session):
    themoviedb(
        responses, '/tv/95792', TvApiResponseFactory(name='Pocket Monsters').dict()
    )
    themoviedb(responses, '/tv/95792/external_ids', {'imdb_id': 'ttwhatever'})
    themoviedb(
        responses,
        '/tv/95792/season/1',
        {
            'episodes': [
                {'id': 1, 'name': "Pikachu is Born!", 'episode_number': 1},
                {'id': 2, 'name': "Satoshi, Go, and Lugia Go!", 'episode_number': 2},
            ]
        },
    )

    magnet = 'magnet:?xt=urn:btih:dacf233f2586b49709fd3526b390033849438313&dn=%5BSome-Stuffs%5D_Pocket_Monsters_%282019%29_002_%281080p%29_%5BCCBE335E%5D.mkv&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce'

    res = await test_client.post(
        '/api/download',
        json=[{'magnet': magnet, 'tmdb_id': 95792, 'season': '1', 'episode': '2'}],
    )
    assert res.status_code == 200

    add_torrent.assert_called_with(magnet, 'tv_shows/Pocket Monsters/Season 1')

    download = session.query(Download).first()
    assert download
    assert download.title == 'Satoshi, Go, and Lugia Go!'
    assert download.episode
    assert download.episode.season == 1
    assert download.episode.episode == 2
    assert download.episode.show_title == 'Pocket Monsters'


@mark.asyncio
async def test_download_season_pack(test_client, responses, add_torrent, session):
    themoviedb(responses, '/tv/90000', TvApiResponseFactory(name='Watchmen').dict())
    themoviedb(responses, '/tv/90000/external_ids', {'imdb_id': 'ttwhatever'})

    magnet = 'magnet:?xt=urn:btih:dacf233f2586b49709fd3526b390033849438313&dn=%5BSome-Stuffs%5D_Pocket_Monsters_%282019%29_002_%281080p%29_%5BCCBE335E%5D.mkv&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce'

    res = await test_client.post(
        '/api/download', json=[{'magnet': magnet, 'tmdb_id': 90000, 'season': '1'}]
    )
    assert res.status_code == 200

    add_torrent.assert_called_with(magnet, 'tv_shows/Watchmen/Season 1')

    download = session.query(Download).first()
    assert download
    assert download.title == 'Season 1'
    assert download.episode
    assert download.episode.season == 1
    assert download.episode.episode is None
    assert download.episode.show_title == 'Watchmen'


def shallow(d: Dict):
    return {k: v for k, v in d.items() if not isinstance(v, dict)}


@mark.asyncio
async def test_index(responses, test_client, get_torrent, snapshot, session, user):
    session.add_all(
        [
            create_episode(
                transmission_id=HASH_STRING,
                imdb_id='tt000000',
                season='1',
                tmdb_id=1,
                episode='1',
                title='Hello world',
                show_title='Programming',
                timestamp=datetime(2020, 4, 21),
                added_by=user,
            ),
            create_movie(
                transmission_id='000000000000000000',
                imdb_id='tt0000001',
                tmdb_id=2,
                title='Other world',
                timestamp=datetime(2020, 4, 20),
                added_by=user,
            ),
        ]
    )
    session.commit()

    res = await test_client.get('/api/index')

    assert res.status_code == 200

    snapshot.assert_match(res.json())


@mark.asyncio
async def test_search(responses, test_client):
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

    res = await test_client.get('/api/search?query=chernobyl')
    assert res.status_code == 200
    assert res.json() == [
        {'imdbID': 10000, 'title': 'Chernobyl', 'year': 2019, 'type': 'series',}
    ]


@mark.asyncio
async def test_delete_cascade(test_client: TestClient, session):

    e = EpisodeDetailsFactory()
    session.add(e)
    session.commit()

    assert len(get_episodes(session)) == 1
    assert len(session.query(Download).all()) == 1

    res = await test_client.get(f'/api/delete/series/{e.id}')
    assert res.status_code == 200
    assert res.json() == {}

    session.commit()

    assert len(get_episodes(session)) == 0
    assert len(session.query(Download).all()) == 0


@mark.skip
@mark.asyncio
async def test_select_season(responses: RequestsMock, test_client: TestClient) -> None:
    themoviedb(responses, '/tv/100000', {'number_of_seasons': 1})

    res = await test_client.get('/api/select/100000/season')

    assert res.status_code == 200

    assert res.json()


@mark.asyncio
async def test_foreign_key_integrity(session: Session):

    # invalid fkey_id
    ins = Download.__table__.insert().values(id=1, movie_id=99)
    with raises(IntegrityError):
        session.execute(ins)


@mark.asyncio
async def test_delete_monitor(responses, test_client, session):
    themoviedb(
        responses, '/movie/5', MovieResponseFactory.build(title='Hello World').dict()
    )
    ls = (await test_client.get('/api/monitor')).json()
    assert ls == []

    r = await test_client.post('/api/monitor', json={'tmdb_id': 5, 'type': 'MOVIE'})
    assert r.status_code == 201

    ls = (await test_client.get('/api/monitor')).json()

    assert ls == [
        {
            'type': 'MOVIE',
            'title': 'Hello World',
            'tmdb_id': 5,
            'id': 1,
            'status': False,
            'added_by': 'python',
        }
    ]
    ident = ls[0]['id']

    r = await test_client.delete(f'/api/monitor/{ident}')
    assert r.status_code == 200

    ls = (await test_client.get('/api/monitor')).json()
    assert ls == []


@mark.asyncio
async def test_stats(test_client, session):
    user1 = UserFactory(username='user1')
    user2 = UserFactory(username='user2')

    session.add_all(
        [
            EpisodeDetailsFactory(download__added_by=user1),
            EpisodeDetailsFactory(download__added_by=user2),
            MovieDetailsFactory(download__added_by=user1),
        ]
    )
    session.commit()

    assert (await test_client.get('/api/stats')).json() == [
        {'user': 'user1', 'values': {'episode': 1, 'movie': 1}},
        {'user': 'user2', 'values': {'episode': 1, 'movie': 0}},
    ]


@patch('rarbg_local.main.get_torrent')
@mark.asyncio
async def test_torrents_error(get_torrent, test_client):
    get_torrent.side_effect = TimeoutError('Timeout!')
    torrents = await test_client.get('/api/torrents')
    assert torrents.status_code == 500
    assert torrents.json() == {'detail': 'Unable to connect to transmission: Timeout!'}


@patch('rarbg_local.main.get_torrent')
@mark.asyncio
async def test_torrents(get_torrent, test_client):
    get_torrent.return_value = {
        'arguments': {
            'torrents': [
                {
                    'hashString': '00000',
                    'files': [
                        {'name': 'movie.mov', 'bytesCompleted': 30, 'length': 30}
                    ],
                    'id': 360,
                    'eta': -1,
                    'percentDone': 1,
                }
            ]
        }
    }
    torrents = await test_client.get('/api/torrents')
    assert torrents.json() == {
        '00000': {
            'hashString': '00000',
            'files': [{'name': 'movie.mov', 'bytesCompleted': 30, 'length': 30}],
            'eta': -1,
            'id': 360,
            'percentDone': 1.0,
        }
    }


@mark.skip
@mark.asyncio
async def test_manifest(test_client):
    r = await test_client.get('/api/manifest.json')

    assert 'name' in r.json()


@mark.asyncio
async def test_movie(test_client, snapshot, responses):
    themoviedb(responses, '/movie/1', {'title': 'Hello', 'imdb_id': 'tt0000000'})
    r = await test_client.get('/api/movie/1')
    assert r.status_code == 200

    snapshot.assert_match(r.json())


@mark.asyncio
async def test_openapi(test_client, snapshot):
    r = await test_client.get('/openapi.json')
    assert r.status_code == 200

    snapshot.assert_match(r.json())


@mark.asyncio
async def test_stream(test_client, responses):
    themoviedb(responses, '/tv/1/external_ids', {'imdb_id': 'tt00000'})
    root = 'https://torrentapi.org/pubapi_v2.php?mode=search&ranked=0&limit=100&format=json_extended&app_id=Sonarr'
    add_json(responses, 'GET', root + '&get_token=get_token', {'token': 'aaaaaaa'})

    for i in ['41', '49', '18']:
        add_json(
            responses,
            'GET',
            f'{root}&token=aaaaaaa&search_imdb=tt00000&search_string=S01E01&category={i}',
            {
                'torrent_results': [
                    {'seeders': i, 'title': i, 'download': '', 'category': ''}
                ]
            },
        )

    r = await test_client.get('/api/stream/series/1?season=1&episode=1&source=rarbg')

    assert r.status_code == 200, r.json()

    data = r.text.split('\n\n')
    assert data
    assert data.pop(-1) == ''
    assert data.pop(-1) == 'data:'

    datum = [json.loads(line[len('data: ') :]) for line in data]

    datum = sorted(datum, key=lambda item: item['seeders'])

    assert datum == [
        {
            'source': 'rarbg',
            'seeders': 18,
            'title': '18',
            'download': '',
            'category': '',
            'episode_info': {'seasonnum': '1', 'epnum': '1'},
        },
        {
            'source': 'rarbg',
            'seeders': 41,
            'title': '41',
            'download': '',
            'category': '',
            'episode_info': {'seasonnum': '1', 'epnum': '1'},
        },
        {
            'source': 'rarbg',
            'seeders': 49,
            'title': '49',
            'download': '',
            'category': '',
            'episode_info': {'seasonnum': '1', 'epnum': '1'},
        },
    ]


@mark.asyncio
async def test_schema(snapshot):

    snapshot.assert_match(SearchResponse.schema())


@mark.skipif("not os.path.exists('app/build/index.html')")
@mark.parametrize('uri', ['/', '/manifest.json'])
@mark.asyncio
async def test_static(uri, test_client):
    r = await test_client.get(uri)
    assert r.status_code == 200
