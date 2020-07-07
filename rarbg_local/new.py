import re
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, validator

from .db import Monitor, db

app = FastAPI()


class MediaType(Enum):
    SERIES = 'series'
    MOVIE = 'movie'


class Orm(BaseModel):
    class Config:
        orm_mode = True


class DownloadResponse(Orm):
    id: int


class DownloadPost(Orm):
    magnet: str
    tmdb_id: int
    season: Optional[int] = None
    episode: Optional[int] = None

    _valid_magnet = validator('magnet')(lambda field: re.search(r'^magnet:', field))


class ITorrent(BaseModel):
    download: str


@app.post('/download', response_model=DownloadResponse)
def download_post(download: DownloadPost):
    ...


class MonitorPost(Orm):
    tmdb_id: int
    type: MediaType


class MonitorGet(MonitorPost):
    id: int
    title: str
    added_by: str


monitor_ns = APIRouter()


@monitor_ns.get('', tags=['monitor'], response_model=List[MonitorGet])
def monitor_get():
    return db.session.query(Monitor).all()


@monitor_ns.delete('/<monitor_id>', tags=['monitor'])
def monitor_delete(monitor_id: int):
    ...


@monitor_ns.post('', tags=['monitor'], response_model=MonitorGet)
def monitor_post(monitor: MonitorPost):
    m = db.Monitor(**monitor.vars())

    db.session.add(m)
    db.session.commit()

    return m


app.include_router(monitor, prefix='/monitor')
