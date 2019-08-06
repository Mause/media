import json
from typing import Optional
from urllib.parse import urlencode, urlparse

from pytest import fixture, mark
from flask import url_for
from selenium.webdriver import Chrome

from test_integration import cache_clear
from main import create_app


@fixture
def free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@fixture
def mock_transmission(free_port):
    from mock_transmission import app

    server = LiveServer(app, 'localhost', free_port, True)
    server.start()
    yield server
    server.stop()


@fixture
def app(mock_transmission):
    yield create_app(
        {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'ENV': 'development',
            'TESTING': True,
            'TRANSMISSION_URL': mock_transmission.url('/transmission/rpc'),
        }
    )


def test_mock(mock_transmission):
    import requests

    url = mock_transmission.url('/transmission/rpc')
    r = requests.get(url)
    assert r.status_code == 200
    assert 'is-mock' in r.headers


@fixture
def server_url(live_server):
    return live_server.url()


@fixture
def capabilities(capabilities):
    capabilities['loggingPrefs'] = {'performance': 'ALL'}
    return capabilities


@fixture
def webdriver(request, selenium):
    try:
        yield selenium
    finally:
        node = request.node
        if hasattr(node, 'rep_call') and node.rep_call.failed:
            # Make the screen-shot if test failed:
            selenium.save_screenshot(
                f'screenshots/{node.name}-{time.time()}.png'
            )

        selenium.quit()


def click_link(webdriver: Chrome, text: str) -> None:
    webdriver.find_element_by_link_text(text).click()


def search(webdriver: Chrome, text: str) -> None:
    form = webdriver.find_element_by_tag_name('form')
    form.find_element_by_name('query').send_keys(text)
    form.submit()


def test_simple(server_url: str, webdriver: Chrome) -> None:
    get(webdriver, server_url)

    search(webdriver, 'chernobyl')

    click_link(webdriver, 'Chernobyl (2019)')
    click_link(webdriver, 'Season 1')
    click_link(webdriver, '1:23:45')

    check_download_link(
        webdriver,
        'Chernobyl.S01E01.iNTERNAL.1080p.WEB.H264-EDHD[rartv]',
        server_url
        + 'download/series?'
        + urlencode(
            {
                'magnet': 'magnet:?xt=urn:btih:0a49edcbe6cfca62a7b8b24a7f60094b697aa2e9&dn=Chernobyl.S01E01.iNTERNAL.1080p.WEB.H264-EDHD%5Brartv%5D&tr=http%3A%2F%2Ftracker.trackerfix.com%3A80%2Fannounce&tr=udp%3A%2F%2F9.rarbg.me%3A2710&tr=udp%3A%2F%2F9.rarbg.to%3A2710&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce',
                'imdb_id': 'tt7366338',
                'titles': '1:23:45',
                'season': '1',
                'episode': '1',
            }
        ),
    )


def check_download_link(webdriver: Chrome, text: str, expected: str) -> None:
    anchor = webdriver.find_element_by_partial_link_text(text).get_attribute(
        'href'
    )
    assert urlparse(anchor) == urlparse(expected)


def check_no_error(webdriver: Chrome) -> None:
    h3 = [el.text for el in webdriver.find_elements_by_tag_name('h3')]
    assert h3 == []


def get(webdriver: Chrome, url: str) -> None:
    webdriver.get(url)
    assert get_status_code(webdriver) == 200
    check_no_error(webdriver)


def get_status_code(webdriver: Chrome) -> Optional[int]:
    for entry in webdriver.get_log("performance"):
        message = json.loads(entry['message'])["message"]

        if message["method"] == "Network.responseReceived":
            response = message["params"]["response"]

            if webdriver.current_url == response["url"]:
                return int(response["status"])

    return None


def test_movie(server_url: str, webdriver: Chrome) -> None:
    get(webdriver, server_url)

    search(webdriver, 'pikachu')

    click_link(webdriver, 'Pokémon Detective Pikachu (2019)')

    check_download_link(
        webdriver,
        'Pokemon.Detective.Pikachu.2019.1080p.BluRay.x264-AAA 1265',
        server_url
        + 'download/movie?'
        + urlencode(
            {
                'magnet': 'magnet:?xt=urn:btih:13bcfe725c0f663f439478d160ad59891a0475de&dn=Pokemon.Detective.Pikachu.2019.1080p.HDRip.x264.AAC2.0-STUTTERSHIT&tr=http%3A%2F%2Ftracker.trackerfix.com%3A80%2Fannounce&tr=udp%3A%2F%2F9.rarbg.me%3A2710&tr=udp%3A%2F%2F9.rarbg.to%3A2710&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce',
                'imdb_id': 'tt5884052',
                'titles': 'Pokémon Detective Pikachu',
            }
        ),
    )
