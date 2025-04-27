from datetime import date, datetime
from enum import Enum
from functools import reduce
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, constr
from pydantic.main import _missing
from pydantic.utils import GetterDict

from .db import MonitorMediaType
from .types import TmdbId


class Orm(BaseModel):
    class Config:
        orm_mode = True


T = TypeVar('T')


def map_to(config: Dict[str, str]) -> Type:
    class Config:
        class getter_dict(GetterDict):
            def get(self, name: Any, default: Optional[Any] = None) -> Any:
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
    KICKASS = 'kickass'
    HORRIBLESUBS = 'horriblesubs'
    RARBG = 'rarbg'
    TORRENTS_CSV = 'torrentscsv'
    NYAA_SI = 'nyaasi'
    PIRATEBAY = 'piratebay'


class EpisodeInfo(BaseModel):
    seasonnum: int
    epnum: Optional[int]


class ITorrent(BaseModel):
    source: ProviderSource
    title: str
    seeders: int
    download: str
    category: str
    episode_info: Optional[EpisodeInfo] = None


class UserSchema(Orm):
    username: str
    first_name: str


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
    tmdb_id: TmdbId
    type: MonitorMediaType


class UserShim(Orm):
    username: str


class MonitorGet(MonitorPost):
    id: int
    title: str
    added_by: str
    status: bool = False

    Config = map_to({'added_by': 'added_by.username'})


class DownloadPost(BaseModel):
    tmdb_id: TmdbId
    magnet: constr(regex=r'^magnet:')  # type: ignore
    season: Optional[int] = None
    episode: Optional[int] = None


class Episode(BaseModel):
    name: str
    id: int
    episode_number: int
    air_date: Optional[date]


class TvSeasonResponse(BaseModel):
    episodes: List[Episode]


class SeasonMeta(BaseModel):
    episode_count: int
    season_number: int


class TvBaseResponse(BaseModel):
    number_of_seasons: int
    seasons: List[SeasonMeta]


class TvResponse(TvBaseResponse):
    imdb_id: Optional[str]
    title: str


class TvApiResponse(TvBaseResponse):
    name: str


class MediaType(Enum):
    SERIES = 'series'
    MOVIE = 'movie'


class SearchResponse(BaseModel):
    title: str
    type: MediaType
    year: Optional[int]
    imdbID: int


class DownloadResponse(Orm):
    id: int


class MovieResponse(BaseModel):
    title: str
    imdb_id: str


class InnerTorrent(BaseModel):
    class InnerTorrentFile(BaseModel):
        bytesCompleted: int
        length: int
        name: str

    eta: int
    hashString: str
    id: int
    percentDone: float
    files: List[InnerTorrentFile]
