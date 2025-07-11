import json
import socket
from contextlib import closing
from pathlib import Path
from typing import Generator, Never, Optional
from urllib.parse import urlencode, urlparse

from fastapi import FastAPI
from pytest import fixture, mark
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from ..new import create_app
from ..settings import Settings, get_settings

HERE = Path(__name__).resolve().absolute().parent

pytestmark = mark.skip


class LiveServer:
    def __init__(
        self, app: FastAPI, host: str, port: int, reload: bool = False
    ) -> None:
        self.app = app
        self.host = host
        self.port = port
        self.reload = reload

    def start(self) -> Never:
        raise NotImplementedError

    def stop(self) -> Never:
        raise NotImplementedError

    def url(self, path: str = '') -> str:
        return f'http://{self.host}:{self.port}{path}'


@fixture
def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@fixture
def mock_transmission(free_port: int) -> Generator[LiveServer, None, None]:
    from .mock_transmission import app

    server = LiveServer(app, 'localhost', free_port, True)
    server.start()
    yield server
    server.stop()


@fixture
def app(mock_transmission: LiveServer) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url='sqlite:///:memory:',
        transmission_url=mock_transmission.url('/transmission/rpc'),
    )
    return app


def test_mock(mock_transmission: LiveServer) -> None:
    import requests

    url = mock_transmission.url('/transmission/rpc')
    r = requests.get(url)
    assert r.status_code == 200
    assert 'is-mock' in r.headers


@fixture
def server_url(live_server: LiveServer) -> str:
    return live_server.url()


@fixture
def capabilities(capabilities: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    capabilities['loggingPrefs'] = capabilities['goog:loggingPrefs'] = {
        'performance': 'ALL'
    }
    return capabilities


def click_link(selenium: Chrome, text: str) -> None:
    try:
        selenium.find_element(By.LINK_TEXT, text).click()
    except Exception as e:
        raise Exception(selenium.current_url) from e


def search(selenium: Chrome, text: str) -> None:
    form = selenium.find_element(By.TAG_NAME, 'form')
    form.find_element(By.NAME, 'query').send_keys(text)
    form.submit()


def test_simple(server_url: str, selenium: Chrome) -> None:
    get(selenium, server_url)

    search(selenium, 'chernobyl')

    click_link(selenium, 'Chernobyl (2019)')
    click_link(selenium, 'Season 1')
    click_link(selenium, '1:23:45')

    anchor = check_download_link(
        selenium,
        'Chernobyl.S01E01.iNTERNAL.1080p.WEB.H264-EDHD[rartv]',
        server_url
        + '/download/series?'
        + urlencode(
            {
                'magnet': (
                    'magnet:?xt=urn:btih:0a49edcbe6cfca62a7b8b24a7f60094b697aa2e9'
                    '&dn=Chernobyl.S01E01.iNTERNAL.1080p.WEB.H264-EDHD%5Brartv%5D'
                    '&tr=http%3A%2F%2Ftracker.trackerfix.com%3A80%2Fannounce'
                    '&tr=udp%3A%2F%2F9.rarbg.me%3A2710'
                    '&tr=udp%3A%2F%2F9.rarbg.to%3A2710'
                    '&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce'
                ),
                'imdb_id': 'tt7366338',
                'titles': '1:23:45',
                'season': '1',
                'episode': '1',
            }
        ),
    )

    anchor.click()

    assert has_download(selenium, '1:23:45')


def check_download_link(selenium: Chrome, text: str, expected: str) -> WebElement:
    anchor = selenium.find_element(By.PARTIAL_LINK_TEXT, text)
    href = anchor.get_attribute('href')
    assert urlparse(href)._asdict() == urlparse(expected)._asdict()

    return anchor


def check_no_error(selenium: Chrome) -> None:
    h3 = [el.text for el in selenium.find_elements(By.CLASS_NAME, 'error')]
    assert h3 == []


def get(selenium: Chrome, url: str) -> None:
    selenium.get(url)
    assert get_status_code(selenium) == 200
    check_no_error(selenium)


def get_status_code(selenium: Chrome) -> Optional[int]:
    for entry in selenium.get_log("performance"):
        message = json.loads(entry['message'])["message"]

        if message["method"] == "Network.responseReceived":
            response = message["params"]["response"]

            if selenium.current_url == response["url"]:
                return int(response["status"])

    return None


def has_download(selenium: Chrome, name: str) -> bool:
    return bool(
        selenium.find_element(By.XPATH, f'.//li/span[contains(text(), "{name}")]')
    )


def test_movie(server_url: str, selenium: Chrome) -> None:
    get(selenium, server_url)

    search(selenium, 'pikachu')

    click_link(selenium, 'Pokémon Detective Pikachu (2019)')

    anchor = check_download_link(
        selenium,
        'Pokemon.Detective.Pikachu.2019.1080p.BluRay.x264-AAA',
        server_url
        + '/download/movie?'
        + urlencode(
            {
                'magnet': (
                    'magnet:?xt=urn:btih:18560491ab3e461ba04fcefda0c49cd1633be12a'
                    '&dn=Pokemon.Detective.Pikachu.2019.1080p.BluRay.x264-AAA'
                    '&tr=http%3A%2F%2Ftracker.trackerfix.com%3A80%2Fannounce'
                    '&tr=udp%3A%2F%2F9.rarbg.me%3A2710'
                    '&tr=udp%3A%2F%2F9.rarbg.to%3A2710&'
                    'tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce'
                ),
                'imdb_id': 'tt5884052',
                'titles': 'Pokémon Detective Pikachu',
            }
        ),
    )

    anchor.click()

    assert has_download(selenium, 'Pokémon Detective Pikachu')
