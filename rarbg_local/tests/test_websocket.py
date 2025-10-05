from collections.abc import AsyncGenerator
from typing import Annotated
from unittest.mock import MagicMock, patch

from async_asgi_testclient import TestClient
from fastapi import Depends, FastAPI
from fastapi.security import OpenIdConnect, SecurityScopes
from healthcheck import HealthcheckCallbackResponse, HealthcheckStatus
from pytest import fixture, mark, raises
from pytest_snapshot.plugin import Snapshot

from ..auth import User, get_current_user
from ..providers import MovieProvider
from ..providers.abc import ITorrent, ProviderSource
from ..types import ImdbId, TmdbId
from ..websocket import BaseRequest, StreamArgs
from .conftest import assert_match_json
from .factories import UserFactory


@mark.asyncio
async def test_websocket_error(test_client: TestClient, snapshot: Snapshot) -> None:
    r = test_client.websocket_connect(
        '/ws',
    )
    await r.connect()
    await r.send_json(
        {
            'request_type': 'stream',
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
            StreamArgs.model_validate(
                {
                    'request_type': 'stream',
                    'tmdb_id': 1,
                    'type': 'movie',
                    'authorization': 'token',
                }
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
