from enum import Enum
from typing import List, Optional

from fastapi import FastAPI
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


class Monitor(Orm):
    id: int
    tmdb_id: int
    type: MediaType


@app.post('/monitor', tags=['monitor'], response_model=List[Monitor])
def monitor_get():
    ...
