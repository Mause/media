import re
from datetime import date
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, validator

from .db import Monitor, db
from .tmdb import get_tv, get_tv_episodes, get_tv_imdb_id

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


tv_ns = APIRouter()


class SeasonMeta(BaseModel):
    episode_count: int
    season_number: int


class TvResponse(BaseModel):
    number_of_seasons: int
    title: str
    imdb_id: str
    seasons: List[SeasonMeta]


@tv_ns.get('/<tmdb_id>', tags=['tv'], response_model=TvResponse)
def api_tv(tmdb_id: int):
    tv = get_tv(tmdb_id)
    return {**tv, 'imdb_id': get_tv_imdb_id(tmdb_id), 'title': tv['name']}


class Episode(BaseModel):
    name: str
    id: int
    episode_number: int
    air_date: Optional[date]


class TvSeasonResponse(BaseModel):
    episodes: List[Episode]


@tv_ns.get('/<tmdb_id>/season/<season>', tags=['tv'], response_model=TvSeasonResponse)
def api_tv_season(tmdb_id: int, season: int):
    return get_tv_episodes(tmdb_id, season)


app.include_router(tv_ns, prefix='/tv')
app.include_router(monitor, prefix='/monitor')
