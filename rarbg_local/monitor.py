import logging
from asyncio import gather
from typing import Annotated

from aiohttp import ClientSession
from aiontfy import Message, Ntfy
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from requests.exceptions import HTTPError
from sentry_sdk.crons import monitor
from sqlalchemy import not_
from sqlalchemy.future import select
from sqlalchemy.orm.session import Session, object_session
from starlette.routing import compile_path, replace_params
from yarl import URL

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
from .utils import non_null
from .websocket import StreamType, _stream

logger = logging.getLogger(__name__)
monitor_ns = APIRouter(tags=['monitor'])


async def get_ntfy():
    async with ClientSession() as session:
        yield Ntfy("https://ntfy.sh", session)


@monitor_ns.get('', response_model=list[MonitorGet])
async def monitor_get(session: Session = Depends(get_db)):
    return session.execute(select(Monitor)).scalars().all()


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
        session.execute(
            select(Monitor).filter_by(tmdb_id=monitor.tmdb_id, type=monitor.type)
        )
        .scalars()
        .one_or_none()
    )
    if not c:
        c = Monitor(
            tmdb_id=monitor.tmdb_id, added_by=user, type=monitor.type, title=media
        )
        session.add(c)
        session.commit()
    return c


class CronResponse[T](BaseModel):
    success: bool
    message: str
    subject: T | None = None


@monitor_ns.post('/cron', status_code=201)
@monitor(monitor_slug='monitor-cron')
async def monitor_cron(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    ntfy: Annotated[Ntfy, Depends(get_ntfy)],
) -> list[CronResponse[MonitorGet]]:
    monitors = (
        session.execute(select(Monitor).filter(not_(Monitor.status))).scalars().all()
    )

    tasks = [check_monitor(request, monitor, session, ntfy) for monitor in monitors]

    results: list[CronResponse] = []
    for result in await gather(*tasks, return_exceptions=True):
        if isinstance(result, BaseException):
            logger.exception('Error checking monitor', exc_info=result)
            results.append(CronResponse(success=False, message=repr(result)))
        else:
            results.append(result)
    return results


async def check_monitor(
    request: Request,
    monitor: Monitor,
    session: Session,
    ntfy: Ntfy,
) -> CronResponse:
    def convert_type(type: MonitorMediaType) -> StreamType:
        if type == MonitorMediaType.MOVIE:
            return 'movie'
        elif type == MonitorMediaType.TV:
            return 'series'
        else:
            raise HTTPException(422, f'Invalid type: {type}')

    typ = monitor.type
    if not typ:
        raise HTTPException(422, f'Invalid type: {monitor.type}')

    season = 1 if typ == MonitorMediaType.TV else None

    has_results = None
    async for result in _stream(
        tmdb_id=monitor.tmdb_id, type=convert_type(typ), season=season
    ):
        has_results = result
        break
    if not has_results:
        message = f'No results for {monitor.title}'
        logger.info(message)
        return CronResponse(success=True, message=message, subject=monitor)

    monitor.status = bool(has_results)

    def name(x):
        return x.name.title()

    message = f'''
{name(monitor.type)} {monitor.title} is now available on {name(has_results.source)}!
'''.strip()

    logger.info(message)

    params: dict[str, Any]
    if typ == MonitorMediaType.MOVIE:
        path = "select/{tmdb_id}/options"
        params = {"tmdb_id": monitor.tmdb_id}
    else:
        path = "select/{tmdb_id}/season/{season}"
        params = {"tmdb_id": monitor.tmdb_id, "season": season}
    conv = compile_path(path)[-1]
    url, qs = replace_params(path, conv, params)

    await ntfy.publish(
        Message(
            topic="ellianas_notifications",
            title="Hello",
            message=message,
            click=URL(
                str(
                    request.url_for(
                        'static',
                        resource=url,
                    )
                )
            ),
        )
    )
    session.commit()

    return CronResponse(success=True, message=message, subject=monitor)
