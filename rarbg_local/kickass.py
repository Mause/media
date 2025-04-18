import logging
import re
import string
from typing import Any, Dict, Iterable, Optional

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError

from .tmdb import get_movie, get_tv


def fetch(url: str) -> Iterable[Dict[str, Any]]:
    try:
        r = requests.get(url)
    except ConnectionError:
        logging.exception('Failed to reach kickass')
        return

    soup = BeautifulSoup(r.content, "lxml")

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
                'seeders': int(
                    row.find('td', {'data-title': "Seed"}).text.replace(',', '')
                ),
            }


def tokenise(name: str) -> str:
    name = name.lower()
    name = re.sub(f'[{string.punctuation}]', '', name)
    name = name.replace(' ', '-')

    return name


async def search_for_tv(
    imdb_id: str, tmdb_id: int, season: int, episode: Optional[int] = None
) -> Iterable[Dict]:
    name = (await get_tv(tmdb_id)).name

    if episode is None:
        key = f'S{season:02d}'
        return (item for item in base(name, imdb_id) if key in item['title'])
    else:
        return fetch(
            f'https://katcr.co/name/search/{tokenise(name)}/i{imdb_id.lstrip("t")}/{season}/{episode}'
        )


def base(name, imdb_id):
    return fetch(f'https://katcr.co/name/{tokenise(name)}/i{imdb_id.lstrip("t")}')


async def search_for_movie(imdb_id: str, tmdb_id: int):
    name = (await get_movie(tmdb_id)).title

    return base(name, imdb_id)
