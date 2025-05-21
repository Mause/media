from typing import Annotated

from fastapi import APIRouter, Depends
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

monitor_ns = APIRouter(tags=['monitor'])


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
