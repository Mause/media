import logging
from asyncio import gather
from typing import Annotated, Generic, TypeVar

from aiohttp import ClientSession
from aiontfy import Message, Ntfy
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from requests.exceptions import HTTPError
from sentry_sdk.crons import monitor
from sqlalchemy import not_
from sqlalchemy.ext.asyncio import AsyncSession, async_object_session
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

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
T = TypeVar('T')


async def get_ntfy():
    async with ClientSession() as session:
        yield Ntfy("https://ntfy.sh", session)


@monitor_ns.get('', response_model=list[MonitorGet])
async def monitor_get(session: Annotated[AsyncSession, Depends(get_db)]):
    return (
        (await session.execute(select(Monitor).options(joinedload(Monitor.added_by))))
        .scalars()
        .all()
    )


@monitor_ns.delete('/{monitor_id}')
async def monitor_delete(
    monitor_id: int, session: Annotated[AsyncSession, Depends(get_db)]
):
    await safe_delete(session, Monitor, monitor_id)

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
    session = non_null(async_object_session(user))  # resolve to db session
    media = await validate_id(monitor.type, monitor.tmdb_id)
    c = (
        (
            await session.execute(
                select(Monitor)
                .filter_by(tmdb_id=monitor.tmdb_id, type=monitor.type)
                .options(joinedload(Monitor.added_by))
            )
        )
        .scalars()
        .one_or_none()
    )
    if not c:
        c = Monitor(
            tmdb_id=monitor.tmdb_id, added_by=user, type=monitor.type, title=media
        )
        session.add(c)
        await session.commit()
        await session.refresh(c, attribute_names=['added_by'])
    return c


class CronResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    subject: T | None = None


@monitor_ns.post('/cron', status_code=201)
@monitor(monitor_slug='monitor-cron')
async def monitor_cron(
    session: Annotated[AsyncSession, Depends(get_db)],
    ntfy: Annotated[Ntfy, Depends(get_ntfy)],
) -> list[CronResponse[MonitorGet]]:
    monitors = (
        (await session.execute(select(Monitor).filter(not_(Monitor.status))))
        .scalars()
        .all()
    )

    tasks = [check_monitor(monitor, session, ntfy) for monitor in monitors]

    results: list[CronResponse] = []
    for result in await gather(*tasks, return_exceptions=True):
        if isinstance(result, BaseException):
            logger.exception('Error checking monitor', exc_info=result)
            results.append(CronResponse(success=False, message=repr(result)))
        else:
            results.append(result)
    return results


async def check_monitor(
    monitor: Monitor,
    session: AsyncSession,
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

    await ntfy.publish(
        Message(
            topic="ellianas_notifications",
            title="Hello",
            message=message,
        )
    )
    await session.commit()

    return CronResponse(success=True, message=message, subject=monitor)
