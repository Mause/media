import json
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Never
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

from aioresponses import aioresponses as Aioresponses
from async_asgi_testclient import TestClient
from fastapi import Depends, FastAPI
from fastapi.security import OpenIdConnect, SecurityScopes
from healthcheck import HealthcheckCallbackResponse, HealthcheckStatus
from lxml.builder import E
from lxml.etree import tostring
from psycopg import OperationalError
from pydantic import BaseModel, SecretStr
from pytest import LogCaptureFixture, MonkeyPatch, fixture, mark, raises
from pytest_snapshot.plugin import Snapshot
from responses import RequestsMock
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError as SQLAOperationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from ..auth import get_current_user
from ..db import MAX_TRIES, Download, User, create_episode, create_movie
from ..health import DiagnosticsRoot
from ..main import get_episodes
from ..models import ITorrent, ProviderSource
from ..new import SearchResponse, Settings, get_settings
from ..providers.abc import MovieProvider
from ..providers.piratebay import PirateBayProvider
from ..tmdb import MovieExternalIds, TvExternalIds
from ..types import ImdbId, TmdbId
from .conftest import add_json, assert_match_json, themoviedb, tolist
from .factories import (
    DownloadPostFactory,
    EpisodeDetailsFactory,
    MovieDetailsFactory,
    MovieResponseFactory,
    TvApiResponseFactory,
    UserFactory,
)

if TYPE_CHECKING:
    from lxml.etree import _Element


HASH_STRING = '00000000000000000'


@fixture
def get_torrent() -> Generator[None, None, None]:
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
def add_torrent() -> Generator[MagicMock, None, None]:
    res = {'arguments': {'torrent-added': {'hashString': HASH_STRING}}}
    with patch('rarbg_local.main.torrent_add', return_value=res) as mock:
        yield mock


@patch('rarbg_local.plex.MyPlexAccount')
@patch('rarbg_local.health.transmission')
@mark.asyncio
async def test_diagnostics(
    transmission: MagicMock,
    my_plex_account: MagicMock,
    test_client: TestClient,
    user: User,
    aioresponses: Aioresponses,
    snapshot: Snapshot,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr('rarbg_local.health.getpid', lambda: 1)

    # aioresponses.add('https://horriblesubs.info', 'HEAD')
    # aioresponses.add('https://torrentapi.org', 'HEAD')
    # aioresponses.add('https://katcr.co', 'HEAD')
    aioresponses.add('https://nyaa.si', 'HEAD')
    aioresponses.add('https://torrents-csv.com', 'HEAD')
    aioresponses.add('https://api.jikan.moe/v4', 'GET', body='{}')
    aioresponses.add('https://apibay.org/q.php', 'HEAD')

    transmission.return_value.channel.consumer_tags = ['ctag1']
    transmission.return_value._thread.is_alive.return_value = True

    my_plex_account.return_value.resource.return_value.connect.return_value._baseurl = (
        'http://rushmoore'
    )

    r = await test_client.get(
        '/api/diagnostics',
    )
    assert r.status_code == 200
    root = DiagnosticsRoot.model_validate(r.json())
    snapshot.assert_match(root.model_dump_json(indent=2), 'healthcheck.json')

    for component in root.checks:
        r = await test_client.get(f'/api/diagnostics/{component}')
        r.raise_for_status()
        results = r.json()
        for check in results:
            check.pop('time')

        if component == 'database':
            continue

        snapshot.assert_match(json.dumps(results, indent=2), f'{component}.json')


def stub_movie_external_ids(aioresponses: Aioresponses) -> None:
    tmdb_id = TmdbId(533985)
    themoviedb(
        aioresponses,
        f'/movie/{tmdb_id}/external_ids',
        MovieExternalIds.model_validate(
            {'id': tmdb_id, 'imdb_id': "tt8425034"}
        ).model_dump(),
    )


@mark.asyncio
async def test_download_movie(
    test_client: TestClient,
    responses: RequestsMock,
    aioresponses: Aioresponses,
    add_torrent: MagicMock,
    async_session: AsyncSession,
) -> None:
    themoviedb(
        aioresponses,
        '/movie/533985',
        MovieResponseFactory.build(title='Bit').model_dump(),
    )
    stub_movie_external_ids(aioresponses)

    magnet = 'magnet:...'

    res = await test_client.post(
        '/api/download',
        json=[
            DownloadPostFactory.build(
                magnet=magnet, tmdb_id=533985, is_tv=False
            ).model_dump()
        ],
    )
    assert res.status_code == 200

    add_torrent.assert_called_with(magnet, 'movies')

    download = (await async_session.execute(select(Download))).scalars().first()
    assert download
    assert download.title == 'Bit'


@mark.asyncio
async def test_download(
    test_client: TestClient,
    aioresponses: Aioresponses,
    responses: RequestsMock,
    add_torrent: MagicMock,
    async_session: AsyncSession,
) -> None:
    themoviedb(
        aioresponses,
        '/tv/95792',
        TvApiResponseFactory.create(name='Pocket Monsters').model_dump(),
    )
    stub_tv_external_ids(aioresponses)
    themoviedb(
        aioresponses,
        '/tv/95792/season/1',
        {
            'episodes': [
                {'id': 1, 'name': "Pikachu is Born!", 'episode_number': 1},
                {'id': 2, 'name': "Satoshi, Go, and Lugia Go!", 'episode_number': 2},
            ]
        },
    )

    magnet = (
        'magnet:?xt=urn:btih:dacf233f2586b49709fd3526b390033849438313'
        '&dn=%5BSome-Stuffs%5D_Pocket_Monsters_%282019%29_002_%281080p%29_%5BCCBE335E%5D.mkv'
        '&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce'
        '&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce'
        '&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce'
        '&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce'
        '&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce'
    )

    res = await test_client.post(
        '/api/download',
        json=[{'magnet': magnet, 'tmdb_id': 95792, 'season': 1, 'episode': 2}],
    )
    assert res.status_code == 200

    add_torrent.assert_called_with(magnet, 'tv_shows/Pocket Monsters/Season 1')

    download = (
        (
            await async_session.execute(
                select(Download).options(joinedload(Download.episode))
            )
        )
        .scalars()
        .first()
    )
    assert download
    assert download.title == 'Satoshi, Go, and Lugia Go!'
    assert download.episode
    assert download.episode.season == 1
    assert download.episode.episode == 2
    assert download.episode.show_title == 'Pocket Monsters'


@mark.asyncio
async def test_download_duplicate(
    test_client: TestClient,
    aioresponses: Aioresponses,
    responses: RequestsMock,
    add_torrent: MagicMock,
    async_session: AsyncSession,
) -> None:
    '''
    https://elliana-may.sentry.io/issues/6715511623/?project=1869914
    '''
    themoviedb(
        aioresponses,
        '/tv/95792',
        TvApiResponseFactory.create(name='Pocket Monsters').model_dump(),
    )
    stub_tv_external_ids(aioresponses)
    themoviedb(
        aioresponses,
        '/tv/95792/season/1',
        {
            'episodes': [
                {'id': 1, 'name': "Pikachu is Born!", 'episode_number': 1},
                {'id': 2, 'name': "Satoshi, Go, and Lugia Go!", 'episode_number': 2},
            ]
        },
    )

    magnet = (
        'magnet:?xt=urn:btih:dacf233f2586b49709fd3526b390033849438313'
        '&dn=%5BSome-Stuffs%5D_Pocket_Monsters_%282019%29_002_%281080p%29_%5BCCBE335E%5D.mkv'
        '&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce'
        '&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce'
        '&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce'
        '&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce'
        '&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce'
    )

    hash_string = "HASHHASHHASH"
    EpisodeDetailsFactory.create(
        download__transmission_id=hash_string,
        download__title='Satoshi, Go, and Lugia Go!',
        season=1,
        episode=2,
        show_title='Pocket Monsters',
    )
    await async_session.commit()

    add_torrent.return_value = {
        "arguments": {"torrent-added": {"hashString": hash_string}}
    }

    res = await test_client.post(
        '/api/download',
        json=[{'magnet': magnet, 'tmdb_id': 95792, 'season': '1', 'episode': '2'}],
    )
    assert res.status_code == 200

    add_torrent.assert_called_with(magnet, 'tv_shows/Pocket Monsters/Season 1')

    download = (
        (
            await async_session.execute(
                select(Download).options(joinedload(Download.episode))
            )
        )
        .scalars()
        .first()
    )
    assert download
    assert download.title == 'Satoshi, Go, and Lugia Go!'
    assert download.episode
    assert download.episode.season == 1
    assert download.episode.episode == 2
    assert download.episode.show_title == 'Pocket Monsters'


@mark.asyncio
async def test_download_season_pack(
    test_client: TestClient,
    aioresponses: Aioresponses,
    responses: RequestsMock,
    add_torrent: MagicMock,
    async_session: AsyncSession,
) -> None:
    tmdb_id = TmdbId(90000)
    themoviedb(
        aioresponses,
        f'/tv/{tmdb_id}',
        TvApiResponseFactory.create(name='Watchmen').model_dump(),
    )
    stub_tv_external_ids(aioresponses, tmdb_id=tmdb_id)

    magnet = (
        'magnet:?xt=urn:btih:dacf233f2586b49709fd3526b390033849438313'
        '&dn=%5BSome-Stuffs%5D_Pocket_Monsters_%282019%29_002_%281080p%29_%5BCCBE335E%5D.mkv'
        '&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce'
        '&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce'
        '&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce'
        '&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce'
        '&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce'
    )

    res = await test_client.post(
        '/api/download', json=[{'magnet': magnet, 'tmdb_id': tmdb_id, 'season': 1}]
    )
    assert res.status_code == 200

    add_torrent.assert_called_with(magnet, 'tv_shows/Watchmen/Season 1')

    download = (
        (
            await async_session.execute(
                select(Download).options(joinedload(Download.episode))
            )
        )
        .scalars()
        .first()
    )
    assert download
    assert download.title == 'Season 1'
    assert download.episode
    assert download.episode.season == 1
    assert download.episode.episode is None
    assert download.episode.show_title == 'Watchmen'


def shallow(d: dict) -> dict:
    return {k: v for k, v in d.items() if not isinstance(v, dict)}


@mark.asyncio
async def test_index(
    responses: RequestsMock,
    aioresponses: Aioresponses,
    test_client: TestClient,
    get_torrent: MagicMock,
    snapshot: Snapshot,
    async_session: AsyncSession,
    user: User,
) -> None:
    async_session.add_all(
        [
            create_episode(
                transmission_id=HASH_STRING,
                imdb_id='tt000000',
                season=1,
                tmdb_id=1,
                episode=1,
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
            create_episode(
                transmission_id=HASH_STRING[:-1] + 'a',
                imdb_id='tt0000002',
                season=1,
                episode=None,
                tmdb_id=3,
                title='Hello world 2',
                show_title='Coding',
                timestamp=datetime(2020, 4, 21),
                added_by=user,
            ),
        ]
    )
    await async_session.commit()

    aioresponses.add(
        'https://api.themoviedb.org/3/tv/3/season/1',
        method='GET',
        body=json.dumps(
            {
                "episodes": [
                    {"name": "The Pilot", "id": "00000", "episode_number": 1},
                    {"name": "The Fight", "id": "00001", "episode_number": 2},
                ]
            }
        ),
    )

    res = await test_client.get('/api/index')

    assert res.status_code == 200

    assert_match_json(snapshot, res, 'index.json')


@mark.asyncio
async def test_search(
    aioresponses: Aioresponses, test_client: TestClient, snapshot: Snapshot
) -> None:
    themoviedb(
        aioresponses,
        '/search/multi',
        {
            'results': [
                {
                    'id': 10000,
                    'media_type': 'tv',
                    'name': 'Chernobyl',
                    'first_air_date': '2019-01-01',
                },
                {
                    "backdrop_path": "/puScb607D1bMqZFL6un10sFyxX2.jpg",
                    "id": 525928,
                    "title": "Chernobyl.3828",
                    "original_title": "Чорнобиль.3828",
                    "overview": "Military people call such places \"FRONTLINE\"",
                    "poster_path": "/gYJKdUHxr3qNb6Vu2lyUfz8LESF.jpg",
                    "media_type": "movie",
                    "adult": False,
                    "original_language": "ru",
                    "genre_ids": [99, 36],
                    "popularity": 0.1543,
                    "release_date": "2011-12-14",
                    "video": False,
                    "vote_average": 0.0,
                    "vote_count": 0,
                },
                {
                    "id": 11111,
                    "title": "Unknown",
                    "media_type": "movie",
                    "release_date": "",
                },
                {
                    "id": 98628,
                    "name": "Kim Fields",
                    "original_name": "Kim Fields",
                    "media_type": "person",
                    "adult": False,
                    "popularity": 2.4103,
                    "gender": 1,
                    "known_for_department": "Acting",
                    "profile_path": "/nfotrIITrn6kP1GodAFPKg64kMD.jpg",
                },
            ]
        },
        query='&query=chernobyl',
    )

    res = await test_client.get('/api/search?query=chernobyl')
    assert res.status_code == 200
    assert_match_json(snapshot, res, 'search.json')


@mark.asyncio
async def test_delete_cascade(
    test_client: TestClient, async_session: AsyncSession
) -> None:
    async def check() -> tuple[int, int]:
        return (
            len(await get_episodes(async_session)),
            len((await async_session.execute(select(Download))).scalars().all()),
        )

    e = EpisodeDetailsFactory.create()
    async_session.add(e)
    await async_session.commit()

    assert await check() == (1, 1)

    res = await test_client.get(f'/api/delete/series/{e.id}')
    assert res.status_code == 200
    assert res.json() == {}

    assert await check() == (0, 0)


@mark.asyncio
async def test_season_info(
    aioresponses: Aioresponses, test_client: TestClient, snapshot: Snapshot
) -> None:
    themoviedb(
        aioresponses,
        '/tv/100000/season/1',
        {'episodes': [{'name': 'The Pilot', 'id': '00000', 'episode_number': 1}]},
    )

    res = await test_client.get('/api/tv/100000/season/1')

    assert res.status_code == 200

    assert_match_json(snapshot, res, 'season_1.json')


@mark.asyncio
async def test_select_season(
    aioresponses: Aioresponses, test_client: TestClient, snapshot: Snapshot
) -> None:
    tmdb_id = TmdbId(100000)
    themoviedb(
        aioresponses,
        f'/tv/{tmdb_id}',
        {
            'number_of_seasons': 1,
            'seasons': [{'episode_count': 1, 'season_number': 1}],
            'name': 'hello',
        },
    )
    stub_tv_external_ids(aioresponses, tmdb_id=tmdb_id)

    res = await test_client.get(f'/api/tv/{tmdb_id}')

    assert res.status_code == 200

    assert_match_json(snapshot, res, f'tv_{tmdb_id}.json')


@mark.asyncio
async def test_foreign_key_integrity(async_session: AsyncSession) -> None:
    # invalid fkey_id
    with raises(IntegrityError):
        ins = Download(id=1, movie_id=99)
        async_session.add(ins)
        await async_session.commit()


@mark.asyncio
async def test_stats(test_client: TestClient, async_session: AsyncSession) -> None:
    user1 = UserFactory.create(username='user1')
    user2 = UserFactory.create(username='user2')

    async_session.add_all(
        [
            EpisodeDetailsFactory.create(download__added_by=user1),
            EpisodeDetailsFactory.create(download__added_by=user2),
            MovieDetailsFactory.create(download__added_by=user1),
        ]
    )
    await async_session.commit()

    assert (await test_client.get('/api/stats')).json() == [
        {'user': 'user1', 'values': {'episode': 1, 'movie': 1}},
        {'user': 'user2', 'values': {'episode': 1, 'movie': 0}},
    ]


@patch('rarbg_local.main.get_torrent')
@mark.asyncio
async def test_torrents_error(get_torrent: MagicMock, test_client: TestClient) -> None:
    get_torrent.side_effect = TimeoutError('Timeout!')
    torrents = await test_client.get('/api/torrents')
    assert torrents.status_code == 500
    assert torrents.json() == {'detail': 'Unable to connect to transmission: Timeout!'}


@patch('rarbg_local.main.get_torrent')
@mark.asyncio
async def test_torrents(get_torrent: MagicMock, test_client: TestClient) -> None:
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
async def test_manifest(test_client: TestClient) -> None:
    r = await test_client.get('/api/manifest.json')

    assert 'name' in r.json()


@mark.asyncio
async def test_movie(
    test_client: TestClient, snapshot: Snapshot, aioresponses: Aioresponses
) -> None:
    themoviedb(aioresponses, '/movie/1', {'title': 'Hello', 'imdb_id': 'tt0000000'})
    r = await test_client.get('/api/movie/1')
    assert r.status_code == 200

    assert_match_json(snapshot, r, 'movie_1.json')


@mark.asyncio
async def test_openapi(test_client: TestClient, snapshot: Snapshot) -> None:
    r = await test_client.get('/openapi.json')
    assert r.status_code == 200

    data = r.json()
    data['info']['version'] = "0.1.0-dev"
    snapshot.assert_match(json.dumps(data, indent=2), 'openapi.json')


def stub_tv_external_ids(
    aioresponses: Aioresponses, *, tmdb_id: TmdbId = TmdbId(95792)
) -> None:
    themoviedb(
        aioresponses,
        f'/tv/{tmdb_id}/external_ids',
        TvExternalIds.model_validate(
            {'id': tmdb_id, 'imdb_id': 'tt00000', 'tvdb_id': None}
        ).model_dump(),
    )


@mark.asyncio
@mark.skip
async def test_stream_rarbg(
    test_client: TestClient,
    responses: RequestsMock,
    aioresponses: Aioresponses,
    snapshot: Snapshot,
) -> None:
    stub_tv_external_ids(aioresponses)
    root = 'https://torrentapi.org/pubapi_v2.php?mode=search&ranked=0&limit=100&format=json_extended&app_id=Sonarr'
    add_json(responses, 'GET', root + '&get_token=get_token', {'token': 'aaaaaaa'})

    for i in ['41', '49', '18']:
        add_json(
            responses,
            'GET',
            f'{root}&token=aaaaaaa&search_imdb=tt00000&search_string=S01E01&category={i}',
            {
                'torrent_results': [
                    {
                        'seeders': i,
                        'title': i,
                        'download': 'magnet:?xt=urn:btih:00000000000000000',
                        'category': '',
                    }
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

    snapshot.assert_match(
        json.dumps(datum, indent=2),
        'stream.json',
    )


@mark.asyncio
async def test_stream(
    test_client: TestClient,
    responses: RequestsMock,
    aioresponses: Aioresponses,
    snapshot: Snapshot,
) -> None:
    stub_tv_external_ids(aioresponses, tmdb_id=TmdbId(1))
    add_json(
        aioresponses,
        'GET',
        'https://apibay.org/q.php?q=tt00000+S01E01',
        [
            {
                'seeders': i,
                'name': f'title {i}',
                'info_hash': '00000000000000000',
                'category': i,
            }
            for i in [201, 202, 205]
        ],
    )

    r = await test_client.get(
        '/api/stream/series/1?season=1&episode=1&source=piratebay'
    )

    assert r.status_code == 200, r.json()

    data = r.text.split('\n\n')
    assert data
    assert data.pop(-1) == ''
    assert data.pop(-1) == 'data:'

    datum = [json.loads(line[len('data: ') :]) for line in data]

    datum = sorted(datum, key=lambda item: item['seeders'])

    snapshot.assert_match(
        json.dumps(datum, indent=2),
        'stream.json',
    )


@mark.asyncio
async def test_schema(snapshot: Snapshot) -> None:
    snapshot.assert_match(
        json.dumps(SearchResponse.model_json_schema(), indent=2), 'schema.json'
    )


@mark.skipif("not os.path.exists('app/build/index.html')")
@mark.parametrize('uri', ['/', '/manifest.json'])
@mark.asyncio
async def test_static(uri: str, test_client: TestClient) -> None:
    r = await test_client.get(uri)
    assert r.status_code == 200


def add_xml(responses: RequestsMock, method: str, url: str, body: '_Element') -> None:
    responses.add(
        method,
        url,
        tostring(body),
        content_type='application/xml',
    )


@mark.asyncio
async def test_plex_redirect(
    test_client: TestClient,
    responses: RequestsMock,
    aioresponses: Aioresponses,
    snapshot: Snapshot,
) -> None:
    add_xml(
        responses,
        'GET',
        'https://plex.tv/api/v2/user',
        E.User(
            E.subscription(),
            E.profile(),
            accessToken='plex_token',
            scrobbleTypes='all',
        ),
    )
    add_xml(
        responses,
        'GET',
        'https://test/',
        E.Root(machineIdentifier="aaaa"),
    )
    add_xml(responses, 'GET', 'https://test/library', E.Library())
    imdb_id = ImdbId('tt00000')
    tmdb_id = TmdbId(10000)
    search = E.Search(
        E.Directory(
            type="show",
            title="Hello World",
            ratingKey="666",
        )
    )
    add_xml(
        responses,
        'GET',
        'https://test/library/all?'
        + urlencode({'guid': f'com.plexapp.agents.imdb://{imdb_id}'}),
        search,
    )
    add_xml(
        responses,
        'GET',
        'https://test/library/all?'
        + urlencode({'guid': f'com.plexapp.agents.tmdb://{tmdb_id}'}),
        search,
    )

    add_xml(
        responses,
        'GET',
        'https://plex.tv/api/v2/resources?includeHttps=1&includeRelay=1',
        E.Resources(
            E.Resource(
                E.connections(E.connection(uri="https://test", secure="True")),
                name="Novell",
                provides="server",
            )
        ),
    )
    stub_tv_external_ids(aioresponses, tmdb_id=tmdb_id)

    r = await test_client.get(f'/api/plex/tv/{tmdb_id}')
    r.raise_for_status()
    assert_match_json(snapshot, r, 'plex_redirect.json')


@mark.asyncio
@mark.skip(reason='Need to figure out retries with async api')
async def test_psycopg2_error(
    monkeypatch: MonkeyPatch,
    fastapi_app: FastAPI,
    test_client: TestClient,
    caplog: LogCaptureFixture,
) -> None:
    async def replacement(*args: Any, **kwargs: Any) -> Never:
        raise OperationalError(message)

    message = 'FATAL:  too many connections for role "wlhdyudesczvwl"'
    monkeypatch.setattr('psycopg.AsyncConnection.connect', replacement)

    do = fastapi_app.dependency_overrides
    cu = do[get_current_user]
    do.clear()
    do.update(
        {
            get_current_user: cu,
            get_settings: lambda: Settings(
                database_url='postgresql:///:memory:',
                plex_token=SecretStr('plex_token'),
            ),
        }
    )

    with raises(SQLAOperationError) as ei:
        await test_client.get('/api/stats')

    assert ei.match(message)

    assert caplog.text.count(message) == MAX_TRIES + 1


class ITorrentList(BaseModel):
    torrents: list[ITorrent]


@mark.asyncio
async def test_piratebay(aioresponses: Aioresponses, snapshot: Snapshot) -> None:
    aioresponses.add(
        'https://apibay.org/q.php?q=tt0000000',
        body=json.dumps(
            [
                {
                    "id": "70178980",
                    "name": "Ancient Aliens 480p x264-mSD",
                    "info_hash": HASH_STRING,
                    "leechers": "0",
                    "seeders": "2",
                    "num_files": "0",
                    "size": "162330051",
                    "username": "jajaja",
                    "added": "1688804411",
                    "status": "vip",
                    "category": "205",
                    "imdb": "",
                }
            ]
        ),
    )
    res = await tolist(
        PirateBayProvider().search_for_movie(
            imdb_id=ImdbId('tt0000000'), tmdb_id=TmdbId(1)
        )
    )

    snapshot.assert_match(
        ITorrentList(torrents=res).model_dump_json(indent=2),
        'piratebay.json',
    )


@mark.asyncio
async def test_websocket_error(test_client: TestClient, snapshot: Snapshot) -> None:
    r = test_client.websocket_connect(
        '/ws',
    )
    await r.connect()
    await r.send_json({})
    snapshot.assert_match(json.dumps(await r.receive_json(), indent=2), 'ws_error.json')


@mark.asyncio
@patch('rarbg_local.websocket.get_movie_imdb_id')
@patch('rarbg_local.providers.get_providers')
async def test_websocket(
    get_providers: MagicMock,
    get_movie_imdb_id: MagicMock,
    test_client: TestClient,
    fastapi_app: FastAPI,
    snapshot: Snapshot,
) -> None:
    class FakeProvider(MovieProvider):
        async def search_for_movie(
            self, imdb_id: ImdbId, tmdb_id: TmdbId
        ) -> AsyncGenerator[ITorrent, None]:
            yield ITorrent(
                source=ProviderSource.PIRATEBAY,
                title="Ancient Aliens 480p x264-mSD",
                seeders=2,
                download="magnet:?xt=urn:btih:00000000000000000",
                category="video - tv shows",
            )

        async def health(self) -> HealthcheckCallbackResponse:
            return HealthcheckCallbackResponse(HealthcheckStatus.PASS, 'all good')

    async def gcu(
        header: Annotated[str, Depends(OpenIdConnect(openIdConnectUrl='https://test'))],
        scopes: SecurityScopes,
    ) -> User:
        assert scopes.scopes == ['openid']
        assert header == 'token'
        return UserFactory.create()

    fastapi_app.dependency_overrides[get_current_user] = gcu
    get_movie_imdb_id.return_value = 'tt0000000'
    get_providers.return_value = [
        FakeProvider(),
    ]

    r = test_client.websocket_connect(
        '/ws',
    )
    await r.connect()
    await r.send_json(
        {
            'tmdb_id': 1,
            'type': 'movie',
            'authorization': 'token',
        }
    )

    snapshot.assert_match(json.dumps(await r.receive_json(), indent=2), 'ws.json')

    with raises(Exception) as e:
        await r.receive_json()

    assert e.value.args[0] == {
        'type': 'websocket.close',
        'code': 1000,
        'reason': 'Finished streaming',
    }
