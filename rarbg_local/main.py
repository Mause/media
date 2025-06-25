import logging
import re
import string
from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures._base import TimeoutError as FutureTimeoutError
from typing import cast

from fastapi.exceptions import HTTPException
from requests.exceptions import ConnectionError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.session import Session, make_transient

from .db import (
    Download,
    EpisodeDetails,
    MovieDetails,
    User,
    create_episode,
    create_movie,
    get_episodes,
)
from .models import Episode, InnerTorrent, SeriesDetails
from .tmdb import get_tv_episodes
from .transmission_proxy import get_torrent, torrent_add
from .utils import non_null, precondition

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def categorise(string: str) -> str:
    if string.startswith('Movies/'):
        return string[7:]
    elif string.startswith('Movs/'):
        return string[5:]
    else:
        return string


full_marker_re = re.compile(r'(S(\d{2})E(\d{2}))')
partial_marker_re = re.compile(r'(S(\d{2}))')
season_re = re.compile(r'\W(S\d{2})\W')
punctuation_re = re.compile(f'[{string.punctuation} ]')


def normalise(episodes: list[Episode], title: str) -> str | None:
    sel = full_marker_re.search(title)
    if not sel:
        sel = season_re.search(title)
        if sel:
            return title

        logger.warn('unable to find marker in %s', title)
        return None

    full, _, i_episode = sel.groups()

    episode = next(
        (
            episode
            for episode in episodes
            if episode.episode_number == int(i_episode, 10)
        ),
        None,
    )
    assert episode

    to_replace = punctuation_re.sub(' ', episode.name)
    to_replace = '.'.join(to_replace.split())
    title = re.sub(to_replace, 'TITLE', title, flags=re.I)

    title = title.replace(full, 'S00E00')

    return title


def extract_marker(title: str) -> tuple[str, str | None]:
    m = full_marker_re.search(title)
    if not m:
        m = partial_marker_re.search(title)
        precondition(m, f'Cannot find marker in: {title}')
        return non_null(m).group(2), None
    return cast(tuple[str, str], tuple(m.groups()[1:]))


def add_single(
    *,
    session: Session,
    magnet: str,
    subpath: str,
    is_tv: bool,
    imdb_id: str,
    tmdb_id: int,
    season: int | None,
    episode: int | None,
    title: str,
    show_title: str | None,
    added_by: User,
) -> MovieDetails | EpisodeDetails:
    res = torrent_add(magnet, subpath)
    arguments = res['arguments']
    logger.info('arguments: %s', arguments)
    if not arguments:
        # the error result shape is really weird
        raise ValueError(res['result'], data={'message': res['result']})

    transmission_id = (
        arguments['torrent-added']
        if 'torrent-added' in arguments
        else arguments['torrent-duplicate']
    )['hashString']

    already = (
        session.execute(select(Download).filter_by(transmission_id=transmission_id))
        .scalars()
        .one_or_none()
    )

    logger.info('does it already exist? %s', already)
    if not already:
        if is_tv:
            precondition(season, 'Season must be provided for tv type')
            return create_episode(
                transmission_id=transmission_id,
                imdb_id=imdb_id,
                season=non_null(season),
                episode=episode,
                title=title,
                tmdb_id=tmdb_id,
                show_title=non_null(show_title),
                added_by=added_by,
            )
        else:
            return create_movie(
                transmission_id=transmission_id,
                imdb_id=imdb_id,
                tmdb_id=tmdb_id,
                title=title,
                added_by=added_by,
            )

    return already.episode if is_tv else already.movie


def groupby[K, V](iterable: Iterable[V], key: Callable[[V], K]) -> dict[K, list[V]]:
    dd: dict[K, list[V]] = defaultdict(list)
    for item in iterable:
        dd[key(item)].append(item)
    return dict(dd)


async def resolve_season(episodes: list[EpisodeDetails]) -> list[EpisodeDetails]:
    if not (len(episodes) == 1 and episodes[0].is_season_pack()):
        return episodes

    pack = episodes[0]
    download = pack.download
    if download.added_by:
        added_by = download.added_by
        make_transient(download.added_by)
    else:
        added_by = None
    common = {
        'imdb_id': download.imdb_id,
        'type': 'episode',
        'tmdb_id': download.tmdb_id,
        'timestamp': download.timestamp,
        'added_by': added_by,
    }
    return [
        EpisodeDetails(
            id=-1,
            download=Download(
                id=-1,
                transmission_id=f'{download.transmission_id}.{episode.episode_number}',
                title=episode.name,
                **common,
            ),
            season=pack.season,
            episode=episode.episode_number,
            show_title=pack.show_title,
        )
        for episode in (
            await get_tv_episodes(pack.download.tmdb_id, pack.season)
        ).episodes
    ]


async def resolve_show(show: list[EpisodeDetails]) -> dict[str, list[EpisodeDetails]]:
    seasons = groupby(show, lambda episode: episode.season)
    return {
        str(number): await resolve_season(
            sorted(season, key=lambda episode: episode.episode or -1)
        )
        for number, season in seasons.items()
    }


async def make_series_details(show: list[EpisodeDetails]) -> SeriesDetails:
    ep = show[0]
    d = ep.download

    return SeriesDetails(
        title=ep.show_title,
        seasons=await resolve_show(show),
        imdb_id=d.imdb_id,
        tmdb_id=d.tmdb_id,
    )


async def resolve_series(session: AsyncSession) -> list[SeriesDetails]:
    # TODO: groupby in db
    episodes = await get_episodes(session)

    return [
        await make_series_details(show)
        for show in groupby(episodes, lambda episode: episode.download.tmdb_id).values()
    ]


def get_keyed_torrents() -> dict[str, InnerTorrent]:
    try:
        return {
            t['hashString']: InnerTorrent.model_validate(t)
            for t in get_torrent()['arguments']['torrents']
        }
    except (
        ConnectionError,
        TimeoutError,
        FutureTimeoutError,
    ) as e:
        logger.exception('Unable to connect to transmission')
        error = f'Unable to connect to transmission: {str(e)}'
        raise HTTPException(500, error)
