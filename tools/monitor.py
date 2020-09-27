import os
import time

import requests
from requests.exceptions import ConnectionError, ReadTimeout
from rich.columns import Columns
from rich.console import Console
from rich_sparklines import Graph

print = Console().print


def get_connections():
    response = requests.post(
        "https://data-api.heroku.com/graphql",
        json={
            "query": "{ postgres(addon_uuid: $addon) { connections } } ",
            "variables": {"addon": "8d550da5-e054-47c2-8a5c-1635d27281ee"},
        },
        headers={'authorization': "Bearer " + open('token.txt').read().strip()},
    ).json()

    if 'errors' in response:
        return '?'

    return int(response['data']['postgres']['connections'].split('/')[0])


def get_pool(key):
    def getter():
        try:
            data = requests.get(
                'https://media.mause.me/api/diagnostics/pool',
                headers={
                    'authorization': (
                        'Bearer ' + open('media_token.txt').read().strip()
                    )
                },
                timeout=1,
            ).json()
        except (ReadTimeout, ConnectionError):
            return '?'

        return data[key]

    return getter


def main():
    graphs = [
        Graph('connections', get_connections),
        *[
            Graph(key, get_pool(key))
            for key in ('size', 'checkedin', 'overflow', 'checkedout')
        ],
    ]
    while True:
        for g in graphs:
            g.update()

        os.system('cls')

        print(Columns(graphs))

        time.sleep(1)


if __name__ == "__main__":
    main()
