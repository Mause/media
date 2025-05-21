import logging
from asyncio import create_task
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from python_ntfy import NtfyClient
from requests.exceptions import HTTPError
from sqlalchemy.orm.session import Session

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
from .types import TmdbId

logger = logging.getLogger(__name__)
monitor_ns = APIRouter(tags=['monitor'])


def get_ntfy():
    ntfy = NtfyClient()
    ntfy._auth = None
    return ntfy


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
    session: Session = Depends(get_db),
):
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
async def monitor_cron(
    session: Annotated[Session, Depends(get_db)],
    ntfy: Annotated[NtfyClient, Depends(get_ntfy)],
):
    monitors = session.query(Monitor).all()

    tasks = [create_task(check_monitor(monitor, session, ntfy)) for monitor in monitors]

    return tasks


async def check_monitor(
    monitor: Monitor,
    session: Session,
    ntfy: NtfyClient,
):
    from .new import _stream

    typ = monitor.type
    if not typ:
        raise HTTPException(422, f'Invalid type: {monitor.type}')

    has_results = None
    async for result in _stream(
        tmdb_id=monitor.tmdb_id,
        type=typ.name,
    ):
        has_results = result
        break
    if not has_results:
        logger.info(f'No results for {monitor.title}')
        return

    monitor.status = bool(has_results)
    message = f'''
{monitor.type} {monitor.title} is now available on {has_results.source}!
'''
    logger.info(message)
    await run_in_threadpool(
        lambda: ntfy.send(topic="ellianas_notifications", markdown=True)
    )
    session.commit()
