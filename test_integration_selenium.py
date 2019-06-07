from urllib.parse import urlencode, urlparse

import selenium.webdriver
from pytest import fixture

url = 'http://cornell.local:5000'


@fixture(scope='module')
def webdriver():
    options = selenium.webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = selenium.webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()


def click_link(webdriver, text):
    webdriver.find_element_by_link_text(text).click()


def search(webdriver, text):
    form = webdriver.find_element_by_tag_name('form')
    form.find_element_by_name('query').send_keys(text)
    form.submit()


def test_simple(webdriver):
    webdriver.get(url)

    search(webdriver, 'chernobyl')

    click_link(webdriver, 'Chernobyl (2019)')
    click_link(webdriver, 'Season 1')
    click_link(webdriver, '1:23:45')

    check_download_link(
        webdriver,
        'Chernobyl.S01E01.iNTERNAL.1080p.WEB.H264-EDHD[rartv]',
        'http://cornell.local:5000/download/series?'
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


def check_download_link(webdriver, text, expected):
    anchor = webdriver.find_element_by_partial_link_text(text).get_attribute(
        'href'
    )
    assert urlparse(anchor) == urlparse(expected)
