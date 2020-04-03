import re
import string

import requests
from bs4 import BeautifulSoup

from .tmdb import get_movie, get_tv, resolve_id


def fetch(url):
    soup = BeautifulSoup(requests.get(url).content, "lxml")

    for i in soup.find_all(
        'div', {'class': 'tab_content', 'id': lambda id: id != 'comments'}
    ):
        resolution = i.attrs['id']

        for row in i.find('table').find('tbody').find_all('tr'):
            magnet = row.find('a', href=lambda href: href.startswith("magnet:")).attrs[
                'href'
            ]
            title = row.find('a', {'class': 'torrents_table__torrent_title'}).text

            yield {
                'title': title.strip(),
                'magnet': magnet,
                'resolution': resolution,
                'seeders': int(row.find('td', {'data-title': "Seed"}).text),
            }


def tokenise(name):
    name = name.lower()
    name = re.sub(f'[{string.punctuation}]', '', name)
    name = name.replace(' ', '-')

    return name


def _search_url(tmdb_id: str, name: str):
    name = tokenise(name)

    return f'https://katcr.co/name/search/{name}/i{tmdb_id.lstrip("t")}'


def search_for_tv(imdb_id: str, tmdb_id: int, season: int, episode: int):
    name = get_tv(tmdb_id)['name']

    return fetch(_search_url(imdb_id, name) + f'/{season}/{episode}')


def search_for_movie(imdb_id: str, tmdb_id: int):
    name = get_movie(tmdb_id)['title']

    return fetch(_search_url(imdb_id, name))
