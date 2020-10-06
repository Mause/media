import graphene
from fastapi import APIRouter, Depends
from graphql.execution.executors.asyncio import AsyncioExecutor
from starlette.graphql import GraphQLApp

from . import tmdb
from .singleton import get

api = APIRouter()


class SeasonMeta(graphene.ObjectType):
    episode_count = graphene.Int()
    season_number = graphene.Int()


class Episode(graphene.ObjectType):
    name = graphene.String()
    id = graphene.ID()
    episode_number = graphene.Int()
    air_date = graphene.Date()


class Season(graphene.ObjectType):
    episodes = graphene.List(Episode)


class Tv(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    number_of_seasons = graphene.Int()
    seasons = graphene.List(SeasonMeta)
    imdb_id = graphene.String(
        resolver=lambda self, context: tmdb.get_tv_imdb_id(self.id)
    )
    season = graphene.Field(
        Season,
        number=graphene.Int(),
        resolver=lambda self, context, number: tmdb.get_tv_episodes(self.id, number),
    )


class Movie(graphene.ObjectType):
    title = graphene.String()
    imdb_id = graphene.String()


class Monitor(graphene.ObjectType):
    name = graphene.String()
    id = graphene.ID()
    type = graphene.String()


class Query(graphene.ObjectType):
    tv = graphene.Field(
        Tv, id=graphene.ID(), resolver=lambda self, context, id: tmdb.get_tv(id)
    )
    movie = graphene.Field(
        Movie, id=graphene.ID(), resolver=lambda self, context, id: tmdb.get_movie(id),
    )
    monitors = graphene.List(Monitor)

    async def resolve_monitors(self, info):
        from .new import Monitor, get_db

        async def _resolve_monitors(session=Depends(get_db)):
            return session.query(Monitor).all()

        request = info.context['request']
        return await get(request.app, _resolve_monitors, request)


class Mutation(graphene.ObjectType):
    add_download = graphene.Field(
        graphene.String,
        magnet=graphene.String(required=True),
        season=graphene.Int(),
        episode=graphene.Int(),
    )

    def resolve_add_download(self, info, magnet, season=None, episode=None):
        t = ''
        if season is not None and episode is not None:
            t = 'specific episode'
        elif season is not None:
            t = 'whole season'
        else:
            t = 'movie'

        return t + ' ' + magnet


g = GraphQLApp(
    schema=graphene.Schema(query=Query, mutation=Mutation),
    executor_class=AsyncioExecutor,
)


async def t(request):
    return await g(request.scope, request._receive, request._send)


api.add_route('/', t, methods=['POST'])
