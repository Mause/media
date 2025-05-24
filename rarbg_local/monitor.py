import logging
from asyncio import gather
from typing import Annotated

from aiohttp import ClientSession
from aiontfy import Message, Ntfy
from fastapi import APIRouter, Depends, HTTPException
from requests.exceptions import HTTPError
from sentry_sdk.crons import monitor
from sqlalchemy import not_
from sqlalchemy.orm.session import Session, object_session

from .auth import security
from .db import (
    Monitor,
    MonitorMediaType,
    User,
    get_db,
    safe_delete,
)
from .models import (
    MonitorGet,
    MonitorPost,
)
from .tmdb import get_movie, get_tv
from .utils import TmdbId, non_null
from .websocket import _stream

logger = logging.getLogger(__name__)
monitor_ns = APIRouter(tags=['monitor'])


async def get_ntfy():
    async with ClientSession() as session:
        yield Ntfy("https://ntfy.sh", session)


@monitor_ns.get('', response_model=list[MonitorGet])
async def monitor_get(session: Session = Depends(get_db)):
    return session.query(Monitor).all()


@monitor_ns.delete('/{monitor_id}')
async def monitor_delete(monitor_id: int, session: Session = Depends(get_db)):
    safe_delete(session, Monitor, monitor_id)

    return {}


async def validate_id(type: MonitorMediaType, tmdb_id: TmdbId) -> str:
    try:
        return (
            (await get_movie(tmdb_id)).title
            if type == MonitorMediaType.MOVIE
            else (await get_tv(tmdb_id)).name
        )
    except HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(422, f'{type.name} not found: {tmdb_id}')
        else:
            raise


@monitor_ns.post('', response_model=MonitorGet, status_code=201)
async def monitor_post(
    monitor: MonitorPost,
    user: Annotated[User, security],
):
    session = non_null(object_session(user))  # resolve to db session session
    media = await validate_id(monitor.type, monitor.tmdb_id)
    c = (
        session.query(Monitor)
        .filter_by(tmdb_id=monitor.tmdb_id, type=monitor.type)
        .one_or_none()
    )
    if not c:
        c = Monitor(
            tmdb_id=monitor.tmdb_id, added_by=user, type=monitor.type, title=media
        )
        session.add(c)
        session.commit()
    return c


@monitor_ns.post('/cron', status_code=201)
@monitor(monitor_slug='monitor-cron')
async def monitor_cron(
    session: Annotated[Session, Depends(get_db)],
    ntfy: Annotated[Ntfy, Depends(get_ntfy)],
):
    monitors = session.query(Monitor).filter(not_(Monitor.status)).all()

    tasks = [check_monitor(monitor, session, ntfy) for monitor in monitors]

    return await gather(*tasks, return_exceptions=True)


async def check_monitor(
    monitor: Monitor,
    session: Session,
    ntfy: Ntfy,
):
    def convert_type(type: MonitorMediaType):
        if type == MonitorMediaType.MOVIE:
            return 'movie'
        elif type == MonitorMediaType.TV:
            return 'tv'
        else:
            raise HTTPException(422, f'Invalid type: {type}')

    typ = monitor.type
    if not typ:
        raise HTTPException(422, f'Invalid type: {monitor.type}')

    has_results = None
    async for result in _stream(tmdb_id=monitor.tmdb_id, type=convert_type(typ)):
        has_results = result
        break
    if not has_results:
        logger.info(f'No results for {monitor.title}')
        return

    monitor.status = bool(has_results)

    def name(x):
        return x.name.title()

    message = f'''
{name(monitor.type)} {monitor.title} is now available on {name(has_results.source)}!
'''.strip()

    logger.info(message)

    await ntfy.publish(
        Message(
            topic="ellianas_notifications",
            title="Hello",
            message=message,
        )
    )
    session.commit()
