import logging
import time
from datetime import datetime

import requests
from requests.exceptions import ConnectionError, ReadTimeout
from rich.columns import Columns
from rich.console import Console, RenderGroup
from rich_sparklines import Graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


def get_connections():
    response = requests.post(
        "https://data-api.heroku.com/graphql",
        json={
            "query": (
                "{ postgres(addon_uuid: \"8d550da5-e054-47c2-8a5c-1635d27281ee\") {"
                " connections } } "
            ),
        },
        headers={'authorization': "Bearer " + open('token.txt').read().strip()},
    ).json()

    if 'errors' in response:
        logger.error('Error fetching connections: %s', response['errors'])
        return '?'

    return int(response['data']['postgres']['connections'].split('/')[0])


def get_pool():
    try:
        data = requests.get(
            'https://media.mause.me/api/diagnostics/pool',
            headers={
                'authorization': ('Bearer ' + open('media_token.txt').read().strip())
            },
            timeout=1,
        ).json()
    except (ReadTimeout, ConnectionError):
        return {}

    return data


def main() -> None:
    data = {}

    graphs = [
        Graph('connections', get_connections),
        *[
            Graph(key, lambda key=key: data.pop(key, '?'))
            for key in ('size', 'checkedin', 'overflow', 'checkedout')
        ],
    ]
    while True:
        data.update(get_pool())
        for g in graphs:
            g.update()

        console.clear()
        console.print(
            RenderGroup(
                Columns(graphs),
                'timestamp: [blue]{}[/], worker: [blue]{}[/]'.format(
                    datetime.now().isoformat(), data.pop('worker_id', '?')
                ),
            )
        )

        time.sleep(1)


if __name__ == "__main__":
    main()
