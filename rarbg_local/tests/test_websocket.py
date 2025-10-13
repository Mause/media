from collections.abc import AsyncGenerator
from typing import Annotated
from unittest.mock import AsyncMock, MagicMock, patch, seal

from aioresponses import aioresponses as AioResponses
from async_asgi_testclient import TestClient
from fastapi import Depends, FastAPI
from fastapi.security import OpenIdConnect, SecurityScopes
from freezegun import freeze_time
from healthcheck import HealthcheckCallbackResponse, HealthcheckStatus
from plexapi.video import Video
from pydantic import SecretStr
from pytest import MonkeyPatch, fixture, mark, raises
from pytest_snapshot.plugin import Snapshot

from ..auth import User, get_current_user
from ..providers import MovieProvider
from ..providers.abc import ITorrent, ProviderSource
from ..tmdb import ExternalIds
from ..types import ImdbId, TmdbId
from ..websocket import BaseRequest, PlexArgs, StreamArgs
from .conftest import add_json, assert_match_json
from .factories import UserFactory


@mark.asyncio
async def test_websocket_error(test_client: TestClient, snapshot: Snapshot) -> None:
    r = test_client.websocket_connect(
        '/ws',
    )
    await r.connect()
    await r.send_json(
        {
            'method': 'stream',
        }
    )
    assert_match_json(snapshot, await r.receive_json(), 'ws_error.json')


@fixture
def mock_current_user(fastapi_app: FastAPI) -> None:
    async def gcu(
        header: Annotated[str, Depends(OpenIdConnect(openIdConnectUrl='https://test'))],
        scopes: SecurityScopes,
    ) -> User:
        assert scopes.scopes == ['openid']
        assert header == 'token'
        return UserFactory.create()

    fastapi_app.dependency_overrides[get_current_user] = gcu


@mark.asyncio
@patch('rarbg_local.websocket.get_movie_imdb_id')
@patch('rarbg_local.providers.get_providers')
async def test_websocket(
    get_providers: MagicMock,
    get_movie_imdb_id: MagicMock,
    test_client: TestClient,
    snapshot: Snapshot,
    mock_current_user: None,
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

    get_movie_imdb_id.return_value = 'tt0000000'
    get_providers.return_value = [
        FakeProvider(),
    ]

    r = test_client.websocket_connect(
        '/ws',
    )
    await r.connect()
    await r.send_json(
        fix_auth(
            StreamArgs(
                method='stream',
                id=1,
                tmdb_id=1,
                type='movie',
                authorization=SecretStr('token'),
            )
        )
    )

    assert_match_json(snapshot, await r.receive_json(), 'ws.json')

    with raises(Exception) as e:
        await r.receive_json()

    assert e.value.args[0] == {
        'type': 'websocket.close',
        'code': 1000,
        'reason': 'Finished streaming',
    }


def fix_auth(mod: BaseRequest) -> dict:
    d = mod.model_dump()
    d['authorization'] = d['authorization'].get_secret_value()
    return d


@mark.asyncio
@freeze_time("2012-01-14")
async def test_websocket_plex(
    test_client: TestClient,
    snapshot: Snapshot,
    mock_current_user: None,
    monkeypatch: MonkeyPatch,
    aioresponses: AioResponses,
) -> None:
    add_json(
        aioresponses,
        method='GET',
        url='https://api.themoviedb.org/3/movie/1/external_ids',
        json_body=ExternalIds(id=0, imdb_id='tt000000').model_dump(mode='json'),
    )

    plex = MagicMock(name='plex')
    plex.machineIdentifier = 'machine_id'
    section = plex.library.section()
    section.getGuid.return_value = MagicMock(
        spec=Video, type='movie', ratingKey=1, title='Movie'
    )

    matches = section.search.return_value[0].matches.return_value
    matches.__bool__.return_value = True
    matches[0].guid = 'moi'
    matches[0].__bool__.return_value = True
    section.agent = 'agent'
    seal(plex)
    monkeypatch.setattr(
        'rarbg_local.websocket.gracefully_get_plex', AsyncMock(return_value=plex)
    )

    r = test_client.websocket_connect(
        '/ws',
    )
    await r.connect()
    await r.send_json(
        fix_auth(
            PlexArgs(
                method='plex',
                id=1,
                tmdb_id=1,
                media_type='movie',
                authorization=SecretStr('token'),
            )
        )
    )

    assert_match_json(snapshot, await r.receive_json(), 'pong.json')
    assert_match_json(snapshot, await r.receive_json(), 'plex.json')
    with raises(Exception) as e:
        await r.receive_json()

    assert e.value.args[0] == {
        'type': 'websocket.close',
        'code': 1000,
        'reason': 'Plex complete',
    }
