import json

from pytest import fixture, hookimpl
from responses import RequestsMock


def themoviedb(responses, path, response, query=''):
    add_json(
        responses,
        'GET',
        f'https://api.themoviedb.org/3{path}?api_key=66b197263af60702ba14852b4ec9b143'
        + query,
        response,
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
