from datetime import date
from typing import Annotated, TypeVar

import strawberry
from dacite import from_dict
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from . import db, tmdb
from .models import MonitorMediaType
from .utils import TmdbId

T = TypeVar('T')


def convert(tv: type[T], data: BaseModel) -> T:
    return from_dict(data_class=tv, data=data.model_dump())


@strawberry.type
class SeasonMeta:
    episode_count: int
    season_number: int


@strawberry.type
class Episode:
    name: str
    id: int
    episode_number: int
    air_date: date


@strawberry.type
class Season:
    episodes: list[Episode]


@strawberry.type
class Tv:
    id: int
    name: str
    number_of_seasons: int
    seasons: list[SeasonMeta]
    imdb_id: str = strawberry.field(resolver=lambda self: tmdb.get_tv_imdb_id(self.id))

    @strawberry.field
    async def season(self, number: int) -> Season:
        return convert(Season, await tmdb.get_tv_episodes(TmdbId(self.id), number))


@strawberry.type
class Movie:
    title: str
    imdb_id: str


@strawberry.type
class User:
    username: str
    first_name: str


@strawberry.type
class Monitor:
    title: str
    id: int
    type: MonitorMediaType
    added_by: User


@strawberry.type
class Query:
    @strawberry.field
    async def tv(self, id: int) -> Tv:
        return convert(Tv, await tmdb.get_tv(TmdbId(id)))

    @strawberry.field
    async def movie(self, id: int) -> Movie:
        return convert(Movie, await tmdb.get_movie(TmdbId(id)))

    @strawberry.field
    async def monitors(self, info: strawberry.Info) -> list[Monitor]:
        return info.context['session'].query(db.Monitor).all()


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_download(
        self, magnet: str, season: int | None = None, episode: int | None = None
    ) -> str:
        t = ''
        if season is not None and episode is not None:
            t = 'specific episode'
        elif season is not None:
            t = 'whole season'
        else:
            t = 'movie'

        return t + ' ' + magnet


async def context_getter(session: Annotated[Session, Depends(db.get_db)]):
    yield {'session': session}


api = GraphQLRouter(
    schema=strawberry.Schema(query=Query, mutation=Mutation),
    context_getter=context_getter,
)
