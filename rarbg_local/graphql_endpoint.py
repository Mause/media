from datetime import date
from typing import Annotated

import strawberry
from fastapi import Depends
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from . import db, tmdb
from .models import MonitorMediaType

ID = int


@strawberry.type
class SeasonMeta:
    episode_count: int
    season_number: int


@strawberry.type
class Episode:
    name: str
    id: strawberry.ID
    episode_number: int
    air_date: date


@strawberry.type
class Season:
    episodes: list[Episode]


@strawberry.type
class Tv:
    id: ID
    name: str
    number_of_seasons: int
    seasons: list[SeasonMeta]
    imdb_id: str = strawberry.field(resolver=lambda self: tmdb.get_tv_imdb_id(self.id))

    @strawberry.field
    def season(self, number: int) -> Season:
        return tmdb.get_tv_episodes(self.id, number)


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
    id: ID
    type: MonitorMediaType
    added_by: User


@strawberry.type
class Query:
    @strawberry.field
    def tv(self, id: ID) -> Tv:
        return tmdb.get_tv(id)

    @strawberry.field
    def movie(self, id: ID) -> Movie:
        return tmdb.get_movie(id)

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
