import logging

import uvloop
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.traceback import install

from ..models import MediaType
from ..tmdb import get_imdb_id, search_themoviedb
from ..utils import Message
from . import search_for_movie, search_for_tv

logger = logging.getLogger(__name__)

install(show_locals=True)


async def main() -> None:
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])

    console = Console()

    table = Table(
        'Source',
        'Title',
        'Seeders',
        'Has magnet',
        show_header=True,
        header_style="bold magenta",
    )

    query = Prompt.ask('Query?', console=console)
    results = (await search_themoviedb(query))[0]
    tmdb_id = results.tmdb_id
    imdb_id = await get_imdb_id(
        'tv' if results.type == MediaType.SERIES else 'movie', tmdb_id
    )

    if results.type == MediaType.MOVIE:
        tasks, queue = await search_for_movie(imdb_id=imdb_id, tmdb_id=tmdb_id)
    elif results.type == MediaType.SERIES:
        tasks, queue = await search_for_tv(
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            season=IntPrompt.ask('Season?', console=console),
            episode=IntPrompt.ask("Episode?", console=console),
        )
    else:
        logger.info('No results')
        return

    while not all(task.done() for task in tasks):
        row = await queue.get()
        if isinstance(row, Message):
            logger.info("message: %s", row)
            continue
        table.add_row(
            row.source.name, row.title, str(row.seeders), str(bool(row.download))
        )

    console.print(table)


if __name__ == "__main__":
    uvloop.run(main())
