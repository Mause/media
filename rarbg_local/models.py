from datetime import datetime
from enum import Enum
from functools import reduce
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from dataclasses_json import DataClassJsonMixin, config
from marshmallow import Schema
from marshmallow import fields as mfields
from pydantic import BaseModel, constr
from pydantic.main import _missing
from pydantic.utils import GetterDict

from .db import EpisodeDetails, MonitorMediaType, MovieDetails


class Orm(BaseModel):
    class Config:
        orm_mode = True


T = TypeVar('T')


def map_to(config: Dict[str, str]) -> Type:
    class Config:
        class getter_dict(GetterDict):
            def get(self, name: Any, default: Any = None) -> Any:
                if name in config:
                    first, *parts = config[name].split('.')
                    v = super().get(first, default)
                    if v is _missing:
                        return v
                    return reduce(getattr, parts, v)
                else:
                    v = super().get(name, default)
                return v

        orm_mode = True

    return Config


class ProviderSource(Enum):
    KICKASS = 'KICKASS'
    HORRIBLESUBS = 'HORRIBLESUBS'
    RARBG = 'RARBG'


class EpisodeInfo(BaseModel):
    seasonnum: Optional[str]
    epnum: Optional[str]


class ITorrent(BaseModel):
    source: ProviderSource
    title: str
    seeders: int
    download: str
    category: str
    episode_info: EpisodeInfo


class UserSchema(Orm):
    username: str


class DownloadSchema(Orm):
    id: int
    tmdb_id: int
    transmission_id: str
    imdb_id: str
    type: str
    title: str
    timestamp: datetime
    added_by: UserSchema


class EpisodeDetailsSchema(Orm):
    id: int
    download: DownloadSchema
    show_title: str
    season: int
    episode: Optional[int]


class SeriesDetails(Orm):
    title: str
    imdb_id: str
    tmdb_id: int
    seasons: Dict[str, List[EpisodeDetailsSchema]]


class MovieDetailsSchema(Orm):
    id: int
    download: DownloadSchema


class IndexResponse(Orm):
    series: List[SeriesDetails]
    movies: List[MovieDetailsSchema]


class DownloadAllResponse(BaseModel):
    packs: List[ITorrent]
    complete: List[Tuple[str, List[ITorrent]]]
    incomplete: List[Tuple[str, List[ITorrent]]]


class Stats(BaseModel):
    episode: int = 0
    movie: int = 0


class StatsResponse(BaseModel):
    user: str
    values: Stats


class MonitorPost(Orm):
    tmdb_id: int
    type: MonitorMediaType


class UserShim(Orm):
    username: str


class MonitorGet(MonitorPost):
    id: int
    title: str
    added_by: str

    Config = map_to({'added_by': 'added_by.username'})


class DownloadPost(BaseModel):
    tmdb_id: int
    magnet: constr(regex=r'^magnet:')  # type: ignore
    season: Optional[str] = None
    episode: Optional[str] = None
