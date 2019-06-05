import time
from pytest import fixture
import selenium.webdriver


@fixture(scope='module')
def webdriver():
    driver = selenium.webdriver.Chrome()
    try:
        yield driver
    finally:
        driver.quit()


url = 'http://cornell.local:5000'


def click_link(webdriver, text):
    link = webdriver.find_elements_by_partial_link_text(text)
    assert link, f'Cannot find link with text "{text}"'
    link[0].click()


def test_simple(webdriver):
    webdriver.get(url)

    # __import__('pdb').set_trace()

    form = webdriver.find_element_by_tag_name('form')

    input_ = form.find_element_by_name('query')

    input_.send_keys('chernobyl')

    form.submit()

    webdriver.find_element_by_xpath

    click_link(webdriver, 'Chernobyl (2019)')
    click_link(webdriver, 'Season 1')
    click_link(webdriver, '1:23:45')

    click_link(webdriver, 'Chernobyl 1080p')
