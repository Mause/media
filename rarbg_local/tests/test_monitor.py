import base64
import json
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, patch

from aioresponses import aioresponses as Aioresponses
from async_asgi_testclient import TestClient
from fastapi import FastAPI
from pytest import mark
from pytest_snapshot.plugin import Snapshot
from sqlalchemy.orm import Session
from yarl import URL

from ..auth import get_current_user
from ..db import Monitor
from ..models import ITorrent, MediaType
from ..new import ProviderSource
from ..types import TmdbId
from .conftest import add_json, assert_match_json, themoviedb
from .factories import ITorrentFactory, MovieResponseFactory, TvApiResponseFactory


@mark.asyncio
async def test_delete_monitor(
    aioresponses: Aioresponses,
    test_client: TestClient,
    session: Session,
    snapshot: Snapshot,
) -> None:
    themoviedb(
        aioresponses,
        '/movie/5',
        MovieResponseFactory.build(title='Hello World').model_dump(),
    )
    themoviedb(
        aioresponses,
        '/tv/5',
        TvApiResponseFactory.build(name='Hello World').model_dump(),
    )
    ls = (await test_client.get('/api/monitor')).json()
    assert ls == []

    r = await test_client.post('/api/monitor', json={'tmdb_id': 5, 'type': 'MOVIE'})
    assert r.status_code == 201

    (
        await test_client.post('/api/monitor', json={'tmdb_id': 5, 'type': 'TV'})
    ).raise_for_status()

    ls = await test_client.get('/api/monitor')

    assert_match_json(snapshot, ls, 'ls.json')

    for item in ls.json():
        r = await test_client.delete(f'/api/monitor/{item["id"]}')
        assert r.status_code == 200

    ls = (await test_client.get('/api/monitor')).json()
    assert ls == []


@mark.asyncio
@patch('rarbg_local.monitor._stream')
async def test_update_monitor(
    stream: MagicMock,
    aioresponses: Aioresponses,
    test_client: TestClient,
    session: Session,
    snapshot: Snapshot,
    fastapi_app: FastAPI,
) -> None:
    themoviedb(
        aioresponses,
        '/movie/5',
        MovieResponseFactory.build(title='Hello World').model_dump(),
    )
    themoviedb(
        aioresponses,
        '/tv/6',
        TvApiResponseFactory.build(title='Hello World').model_dump(),
    )
    add_json(
        aioresponses,
        'POST',
        'https://ntfy.sh',
        {
            'id': '000000-0000-0000-000000000000',
            'time': 1700000000,
            'event': 'message',
            'topic': 'ellianas_notifications',
        },
    )

    r = await test_client.post('/api/monitor', json={'tmdb_id': 5, 'type': 'MOVIE'})
    r.raise_for_status()
    ident = r.json()['id']
    assert r.status_code == 201

    (
        await test_client.post('/api/monitor', json={'tmdb_id': 6, 'type': 'TV'})
    ).raise_for_status()

    async def impl(
        tmdb_id: TmdbId, type: MediaType, season: int, episode: int | None = None
    ) -> AsyncGenerator[ITorrent, None]:
        if tmdb_id == 5:
            yield ITorrentFactory.build(source=ProviderSource.TORRENTS_CSV)
        else:
            raise Exception('Something went wrong')

    stream.side_effect = impl

    del fastapi_app.dependency_overrides[get_current_user]
    r = await test_client.post(
        '/api/monitor/cron',
        headers={'Authorization': 'Basic ' + base64.b64encode(b'hello:world').decode()},
    )
    r.raise_for_status()
    assert_match_json(snapshot, r, 'cron.json')

    monitor = session.get(Monitor, ident)
    assert monitor
    assert monitor.status

    message = aioresponses.requests['POST', URL('https://ntfy.sh')][0]
    snapshot.assert_match(
        json.dumps(
            message.kwargs['json'],
            indent=2,
        ),
        'message.json',
    )
