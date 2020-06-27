from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from dataclasses_json import DataClassJsonMixin, config
from marshmallow import Schema
from marshmallow import fields as mfields

from .db import EpisodeDetails, MovieDetails


class ProviderSource(Enum):
    KICKASS = 'KICKASS'
    HORRIBLESUBS = 'HORRIBLESUBS'
    RARBG = 'RARBG'


@dataclass
class EpisodeInfo(DataClassJsonMixin):
    seasonnum: Optional[str]
    epnum: Optional[str]


@dataclass
class ITorrent(DataClassJsonMixin):
    source: ProviderSource
    title: str
    seeders: int
    download: str
    category: str
    episode_info: EpisodeInfo


class UserSchema(Schema):
    username = mfields.String()


class DownloadSchema(Schema):
    id = mfields.Integer()
    tmdb_id = mfields.Integer()
    transmission_id = mfields.String()
    imdb_id = mfields.String()
    type = mfields.String()
    title = mfields.String()
    timestamp = mfields.DateTime()
    added_by = mfields.Nested(UserSchema)


class EpisodeDetailsSchema(Schema):
    id = mfields.Integer()
    download = mfields.Nested(DownloadSchema)
    show_title = mfields.String(nullable=False)
    season = mfields.Integer(nullable=False)
    episode = mfields.Integer()


@dataclass
class SeriesDetails(DataClassJsonMixin):
    title: str
    imdb_id: str
    tmdb_id: int
    seasons: Dict[str, List[EpisodeDetails]] = field(
        metadata=config(
            mm_field=mfields.Dict(mfields.Integer, mfields.Nested(EpisodeDetailsSchema))
        )
    )


class MovieDetailsSchema(Schema):
    id = mfields.Integer()
    download = mfields.Nested(DownloadSchema)


@dataclass
class IndexResponse(DataClassJsonMixin):
    series: List[SeriesDetails]
    movies: List[MovieDetails] = field(
        metadata=config(mm_field=mfields.List(mfields.Nested(MovieDetailsSchema,)))
    )
