# https://katcr.co/name/search/steven-universe/i3061046/1/1/#1080


import requests
from bs4 import BeautifulSoup


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


def search(tmdb_id: str, season: str, episode: str):
    return fetch(
        f'https://katcr.co/name/search/steven-universe/i{tmdb_id.lstrip("t")}/{season}/{episode}'
    )
