from datetime import date, datetime
from enum import Enum
from typing import Annotated, TypeVar

from pydantic import BaseModel, StringConstraints

from .db import MonitorMediaType
from .utils import TmdbId


class Orm(BaseModel):
    model_config = {'from_attributes': True}


T = TypeVar('T')
MagnetUri = Annotated[str, StringConstraints(pattern=r'^magnet:')]


class ProviderSource(Enum):
    KICKASS = 'kickass'
    HORRIBLESUBS = 'horriblesubs'
    RARBG = 'rarbg'
    TORRENTS_CSV = 'torrentscsv'
    NYAA_SI = 'nyaasi'
    PIRATEBAY = 'piratebay'


class EpisodeInfo(BaseModel):
    seasonnum: int
    epnum: int | None = None


class ITorrent(BaseModel):
    source: ProviderSource
    title: str
    seeders: int
    download: MagnetUri
    category: str
    episode_info: EpisodeInfo | None = None


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
    episode: int | None


class SeriesDetails(Orm):
    title: str
    imdb_id: str
    tmdb_id: int
    seasons: dict[str, list[EpisodeDetailsSchema]]


class MovieDetailsSchema(Orm):
    id: int
    download: DownloadSchema


class IndexResponse(Orm):
    series: list[SeriesDetails]
    movies: list[MovieDetailsSchema]


class DownloadAllResponse(BaseModel):
    packs: list[ITorrent]
    complete: list[tuple[str, list[ITorrent]]]
    incomplete: list[tuple[str, list[ITorrent]]]


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
    added_by: UserSchema
    status: bool = False


class DownloadPost(BaseModel):
    tmdb_id: TmdbId
    magnet: MagnetUri
    season: int | None = None
    episode: int | None = None


class Episode(BaseModel):
    name: str
    id: int
    episode_number: int
    air_date: date | None = None


class TvSeasonResponse(BaseModel):
    episodes: list[Episode]


class SeasonMeta(BaseModel):
    episode_count: int
    season_number: int


class TvBaseResponse(BaseModel):
    number_of_seasons: int
    seasons: list[SeasonMeta]


class TvResponse(TvBaseResponse):
    imdb_id: str | None
    title: str


class TvApiResponse(TvBaseResponse):
    id: int
    name: str


class MediaType(Enum):
    SERIES = 'series'
    MOVIE = 'movie'


class SearchResponse(BaseModel):
    title: str
    type: MediaType
    year: int | None
    tmdb_id: TmdbId


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
    files: list[InnerTorrentFile]
