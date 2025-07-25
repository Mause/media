import json
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from re import Pattern
from typing import Annotated, Any, Protocol

import pytest_asyncio
import uvloop
from aioresponses import aioresponses as Aioresponses
from async_asgi_testclient import TestClient
from fastapi import Depends, FastAPI
from fastapi.security import SecurityScopes
from pytest import fixture
from pytest_snapshot.plugin import Snapshot
from responses import RequestsMock
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..auth import get_current_user
from ..db import (
    Base,
    Role,
    User,
    get_async_db,
    get_async_sessionmaker,
)
from ..new import (
    Settings,
    create_app,
    get_settings,
)
from ..singleton import get
from ..utils import cache_clear
from .factories import session_var


@fixture(scope="session")
def event_loop_policy() -> uvloop.EventLoopPolicy:
    return uvloop.EventLoopPolicy()


@fixture
def fastapi_app(tmp_path: Path) -> FastAPI:
    cache_clear()
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url=str(
            URL.create(
                'sqlite',
                database=str(tmp_path / 'test.db'),
            )
        ),
        plex_token='plex_token',
    )
    return app


@fixture
def clear_cache() -> None:
    cache_clear()


@fixture
def test_client(fastapi_app: FastAPI, clear_cache: None, user: User) -> TestClient:
    async def gcu(
        scopes: SecurityScopes, session: Annotated[AsyncSession, Depends(get_async_db)]
    ) -> User:
        res = (await session.execute(select(User))).scalars().first()
        assert res
        return res

    fastapi_app.dependency_overrides[get_current_user] = gcu
    return TestClient(
        fastapi_app,
        scope={
            'client': ('1.2.3.4', 9000),
        },
    )


@pytest_asyncio.fixture
async def user(async_session: AsyncSession) -> User:
    u = User(username='python', password='', email='python@python.org')
    u.roles = [Role(name='Member')]
    async_session.add(u)
    await async_session.commit()
    await async_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def async_session(
    fastapi_app: FastAPI,
) -> AsyncGenerator[AsyncSession, None]:
    Session = await get(fastapi_app, get_async_sessionmaker)

    async with Session() as session:
        await session.run_sync(lambda s: Base.metadata.create_all(s.bind))
        session_var.set(session.sync_session)
        yield session


def themoviedb(
    responses: RequestsMock | Aioresponses,
    path: str,
    response: list | dict,
    query: str = '',
) -> None:
    add_json(
        responses,
        'GET',
        'https://api.themoviedb.org/3' + path + ("?" + query if query else ""),
        response,
    )


def add_json(
    responses: RequestsMock | Aioresponses,
    method: str,
    url: str | Pattern,
    json_body: Any,
) -> None:
    responses.add(method=method, url=url, body=json.dumps(json_body))


@fixture
def reverse_imdb(responses: RequestsMock) -> None:
    themoviedb(
        responses,
        '/find/tt000000',
        {'tv_results': [{'id': '100000'}]},
        '&external_source=imdb_id',
    )
    themoviedb(
        responses, '/tv/100000', {'name': 'Introductory', 'number_of_seasons': 1}
    )


'''
@hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "rep_" + rep.when, rep)
'''


@fixture(scope='function')
def responses() -> Generator[RequestsMock, None, None]:
    mock = RequestsMock()
    try:
        mock.start()
        yield mock

    finally:
        mock.stop()


@fixture
def aioresponses() -> Generator[Aioresponses, None, None]:
    from aioresponses import aioresponses

    with aioresponses() as e:
        yield e


async def tolist[T](a: AsyncGenerator[T, None]) -> list[T]:
    lst: list[T] = []
    async for t in a:
        lst.append(t)
    return lst


class HasJson(Protocol):
    def json(self) -> dict | list:
        """Method to return JSON data."""


def assert_match_json(snapshot: Snapshot, res: HasJson, name: str) -> None:
    snapshot.assert_match(json.dumps(res.json(), indent=2), name)
