from enum import Enum
from typing import List, Optional

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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


@app.get('/monitor', tags=['monitor'], response_model=List[MonitorGet])
def monitor_get():
    ...


@app.delete('/monitor/<monitor_id>', tags=['monitor'])
def monitor_delete(monitor_id: int):
    ...


@app.post('/monitor', tags=['monitor'], response_model=MonitorGet)
def monitor_post(monitor: MonitorPost):
    ...


@app.get(
    '/stream/<type>/<tmdb_id>',
    response_class=StreamingResponse,
    responses={200: {"model": ITorrent, "content": {'text/event-stream': {}}}},
)
def stream(
    type: MediaType,
    tmdb_id: int,
    season: Optional[int] = None,
    episode: Optional[int] = None,
):
    ...
