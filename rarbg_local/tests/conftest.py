import json
from asyncio import get_event_loop
from collections.abc import AsyncGenerator
from re import Pattern
from typing import TypeVar

import uvloop
from async_asgi_testclient import TestClient
from pytest import fixture, hookimpl
from responses import RequestsMock

from ..db import Base, Role, User, get_db, get_session_local
from ..new import (
    Settings,
    create_app,
    get_current_user,
    get_settings,
)
from ..singleton import get
from ..utils import cache_clear
from .factories import session_var


@fixture(scope="session")
def event_loop_policy():
    return uvloop.EventLoopPolicy()


@fixture
def fastapi_app():
    cache_clear()
    return create_app()


@fixture
def clear_cache():
    cache_clear()


@fixture
def test_client(fastapi_app, clear_cache, user: User) -> TestClient:
    fastapi_app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(fastapi_app)


@fixture
def user(session):
    u = User(username='python', password='', email='python@python.org')
    u.roles = [Role(name='Member')]
    session.add(u)
    session.commit()
    return u


@fixture
def session(fastapi_app):
    fastapi_app.dependency_overrides[get_settings] = lambda: Settings(
        database_url='sqlite:///:memory:',
        plex_token='plex_token',
    )

    Session = get_event_loop().run_until_complete(get(fastapi_app, get_session_local))
    assert hasattr(Session, 'kw'), Session
    engine = Session.kw['bind']
    assert 'sqlite' in repr(engine), repr(engine)
    Base.metadata.create_all(engine)

    with Session() as session:
        fastapi_app.dependency_overrides[get_db] = lambda: session
        session_var.set(session)
        yield session


def themoviedb(responses, path, response, query=''):
    add_json(
        responses,
        'GET',
        'https://api.themoviedb.org/3' + path + ("?" + query if query else ""),
        response,
    )


def add_json(responses, method: str, url: str | Pattern, json_body) -> None:
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


@hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "rep_" + rep.when, rep)


@fixture(scope='function')
def responses():
    mock = RequestsMock()
    try:
        mock.start()
        yield mock

    finally:
        mock.stop()


@fixture
def aioresponses():
    from aioresponses import aioresponses

    with aioresponses() as e:
        yield e


T = TypeVar('T')


async def tolist(a: AsyncGenerator[T, None]) -> list[T]:
    lst: list[T] = []
    async for t in a:
        lst.append(t)
    return lst
