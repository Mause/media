import logging
import os
import traceback
from collections.abc import AsyncGenerator, Callable, Coroutine
from functools import wraps
from typing import (
    Annotated,
    Any,
    Literal,
    Union,
    cast,
)
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from fastapi_utils.openapi import simplify_operation_ids
from plexapi.server import PlexServer
from pydantic import BaseModel
from sqlalchemy import Row, func
from sqlalchemy.ext.asyncio import AsyncSession, async_object_session
from sqlalchemy.future import select
from starlette.staticfiles import StaticFiles

from .auth import security
from .config import commit, production
from .db import (
    Download,
    EpisodeDetails,
    MovieDetails,
    User,
    get_async_db,
    get_db,
    get_movies,
    safe_delete,
)
from .health import router as health
from .main import (
    add_single,
    extract_marker,
    get_keyed_torrents,
    groupby,
    normalise,
    resolve_series,
)
from .models import (
    DownloadAllResponse,
    DownloadPost,
    EpisodeDetailsSchema,
    IndexResponse,
    InnerTorrent,
    ITorrent,
    MediaType,
    MovieDetailsSchema,
    MovieResponse,
    ProviderSource,
    SearchResponse,
    StatsResponse,
    TvResponse,
    TvSeasonResponse,
)
from .monitor import monitor_ns
from .plex import get_imdb_in_plex, get_plex
from .providers import (
    get_providers,
    search_for_tv,
)
from .providers.abc import (
    MovieProvider,
    TvProvider,
)
from .settings import Settings, get_settings
from .singleton import singleton
from .tmdb import (
    get_movie,
    get_movie_imdb_id,
    get_tv,
    get_tv_episode_imdb_id,
    get_tv_episodes,
    get_tv_imdb_id,
    search_themoviedb,
)
from .types import ImdbId, TmdbId
from .utils import Message, non_null
from .websocket import websocket_ns

api = APIRouter()
logger = logging.getLogger(__name__)
logging.getLogger('backoff').handlers.clear()


def generate_plain_text(exc: BaseException) -> str:
    logger.exception('Error occured', exc_info=exc)
    return ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))


@api.get('/delete/{type}/{id}')
async def delete(
    type: MediaType, id: int, session: Annotated[AsyncSession, Depends(get_async_db)]
) -> dict:
    await safe_delete(
        session, EpisodeDetails if type == MediaType.SERIES else MovieDetails, id
    )

    return {}


def eventstream[**P](
    func: Callable[P, AsyncGenerator[BaseModel, None]],
) -> Callable[P, Coroutine[Any, Any, StreamingResponse]]:
    @wraps(func)
    async def decorator(*args: P.args, **kwargs: P.kwargs) -> StreamingResponse:
        async def internal() -> AsyncGenerator[str, None]:
            async for rset in func(*args, **kwargs):
                yield f'data: {rset.model_dump_json()}\n\n'
            yield 'data:\n\n'

        return StreamingResponse(
            internal(),
            media_type="text/event-stream",
        )

    return cast(Callable[P, Coroutine[None, None, StreamingResponse]], decorator)


StreamType = Literal['series', 'movie']


@api.get(
    '/stream/{type}/{tmdb_id}',
    response_class=StreamingResponse,
    responses={200: {"model": ITorrent, "content": {'text/event-stream': {}}}},
)
async def stream(
    type: StreamType,
    tmdb_id: TmdbId,
    source: ProviderSource,
    season: int | None = None,
    episode: int | None = None,
) -> StreamingResponse:
    return await eventstream(stream_impl)(type, tmdb_id, source, season, episode)


async def stream_impl(
    type: StreamType,
    tmdb_id: TmdbId,
    source: ProviderSource,
    season: int | None = None,
    episode: int | None = None,
) -> AsyncGenerator[ITorrent, None]:
    provider = next(
        (provider for provider in get_providers() if provider.type == source),
        None,
    )
    if not provider:
        raise HTTPException(422, 'Invalid provider')

    if type == 'series':
        if not isinstance(provider, TvProvider):
            return

        async for item in provider.search_for_tv(
            await get_tv_imdb_id(tmdb_id), tmdb_id, non_null(season), episode
        ):
            yield item
    else:
        if not isinstance(provider, MovieProvider):
            return

        async for item in provider.search_for_movie(
            await get_movie_imdb_id(tmdb_id), tmdb_id
        ):
            yield item


@api.get(
    '/select/{tmdb_id}/season/{season}/download_all',
    name='select',
)
async def api_select(tmdb_id: TmdbId, season: int) -> DownloadAllResponse:
    tasks, results = await search_for_tv(await get_tv_imdb_id(tmdb_id), tmdb_id, season)

    episodes = (await get_tv_episodes(tmdb_id, season)).episodes

    packs_or_not: dict[bool, list[ITorrent]] = {True: [], False: []}
    while not all(task.done() for task in tasks):
        result = await results.get()
        if isinstance(result, Message):
            logger.info('Got message %s', result)
        else:
            packs_or_not[extract_marker(result.title)[1] is None].append(result)

    packs = sorted(
        packs_or_not.get(True, []), key=lambda result: result.seeders, reverse=True
    )

    grouped_results = groupby(
        packs_or_not.get(False, []), lambda result: normalise(episodes, result.title)
    )
    complete_or_not = groupby(
        grouped_results.items(), lambda rset: len(rset[1]) == len(episodes)
    )

    return DownloadAllResponse(
        packs=packs,
        complete=complete_or_not.get(True, []),
        incomplete=complete_or_not.get(False, []),
    )


@api.post(
    '/download', response_model=list[Union[MovieDetailsSchema, EpisodeDetailsSchema]]
)
async def download_post(
    things: list[DownloadPost],
    added_by: Annotated[User, security],
) -> list[MovieDetails | EpisodeDetails]:
    results: list[MovieDetails | EpisodeDetails] = []

    # work around a fastapi bug
    # see for more details https://github.com/fastapi/fastapi/discussions/6024
    session = non_null(async_object_session(added_by))

    for thing in things:
        is_tv = thing.season is not None

        show_title: str | None
        if is_tv:
            item = await get_tv(thing.tmdb_id)
            if thing.episode is None:
                title = f'Season {thing.season}'
            else:
                episodes = (await get_tv_episodes(thing.tmdb_id, thing.season)).episodes
                episode = next(
                    (
                        episode
                        for episode in episodes
                        if episode.episode_number == thing.episode
                    ),
                    None,
                )
                if not episode:
                    raise ValueError(f'Could not find episode: {thing}')
                title = episode.name

            show_title = item.name
            subpath = f'tv_shows/{item.name}/Season {thing.season}'
        else:
            show_title = None
            title = (await get_movie(thing.tmdb_id)).title
            subpath = 'movies'

        results.append(
            await add_single(
                session=session,
                magnet=thing.magnet,
                imdb_id=(
                    await get_tv_imdb_id(thing.tmdb_id)
                    if is_tv
                    else await get_movie_imdb_id(thing.tmdb_id)
                )
                or '',
                subpath=subpath,
                tmdb_id=thing.tmdb_id,
                season=thing.season,
                episode=thing.episode,
                title=title,
                show_title=show_title,
                is_tv=is_tv,
                added_by=added_by,
            )
        )

    session.add_all(results)
    await session.commit()

    for res in results:
        # TODO: can we do this one call, or in the commit?
        await session.refresh(res, attribute_names=['download'])
        await session.refresh(res.download, attribute_names=['added_by'])

    return results


@api.get('/index')
async def index(
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> IndexResponse:
    return IndexResponse(
        series=await resolve_series(session), movies=await get_movies(session)
    )


@api.get('/stats')
async def stats(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[StatsResponse]:
    async def process(
        added_by_id: int, values: list[Row[tuple[int, str, int]]]
    ) -> StatsResponse:
        user = await session.get(User, added_by_id)
        if not user:
            raise Exception()

        return StatsResponse(
            user=user.username,
            values={type.lower(): value for _, type, value in values},
        )

    keys = Download.added_by_id, Download.type
    query = await session.execute(
        select(*keys, func.count(name='count')).group_by(*keys)
    )

    return [
        await process(added_by_id, values)
        for added_by_id, values in groupby(query, lambda row: row.added_by_id).items()
    ]


@api.get('/movie/{tmdb_id:int}')
async def movie(tmdb_id: TmdbId) -> MovieResponse:
    return await get_movie(tmdb_id)


@api.get('/torrents')
async def torrents() -> dict[str, InnerTorrent]:
    return get_keyed_torrents()


@api.get('/search')
async def search(query: str) -> list[SearchResponse]:
    return await search_themoviedb(query)


tv_ns = APIRouter(tags=['tv'])


@tv_ns.get('/{tmdb_id}')
async def api_tv(tmdb_id: TmdbId) -> TvResponse:
    tv = await get_tv(tmdb_id)
    return TvResponse(
        **tv.model_dump(), imdb_id=await get_tv_imdb_id(tmdb_id), title=tv.name
    )


@tv_ns.get('/{tmdb_id}/season/{season}')
async def api_tv_season(tmdb_id: TmdbId, season: int) -> TvSeasonResponse:
    return await get_tv_episodes(tmdb_id, season)


root = APIRouter()


@singleton
def get_static_files(settings: Settings = Depends(get_settings)) -> StaticFiles:
    return StaticFiles(directory=str(settings.static_resources_path))


@root.get('/redirect/plex/{imdb_id}')
def redirect_to_plex(
    imdb_id: ImdbId, plex: Annotated[PlexServer, Depends(get_plex)]
) -> RedirectResponse:
    dat = get_imdb_in_plex(imdb_id, plex)
    if not dat:
        raise HTTPException(404, 'Not found in plex')

    server_id = plex.machineIdentifier

    return RedirectResponse(
        f'https://app.plex.tv/desktop#!/server/{server_id}/details?'
        + urlencode({'key': f'/library/metadata/{dat.ratingKey}'})
    )


@root.get('/redirect/{type_}/{tmdb_id}')
@root.get(
    '/redirect/{type_}/{tmdb_id}/{season}/{episode}', name='redirect_to_imdb_deep'
)
async def redirect_to_imdb(
    type_: MediaType,
    tmdb_id: TmdbId,
    season: int | None = None,
    episode: int | None = None,
) -> RedirectResponse:
    if type_ == MediaType.MOVIE:
        imdb_id = await get_movie_imdb_id(tmdb_id)
    elif season:
        imdb_id = await get_tv_episode_imdb_id(tmdb_id, season, episode)
    else:
        imdb_id = await get_tv_imdb_id(tmdb_id)

    return RedirectResponse(f'https://www.imdb.com/title/{imdb_id}')


@root.api_route('/{resource:path}', methods=['GET', 'HEAD'], include_in_schema=False)
@root.api_route('/', methods=['GET', 'HEAD'], include_in_schema=False)
async def static(
    request: Request,
    resource: str = '',
    static_files: StaticFiles = Depends(get_static_files),
) -> Response:
    filename = resource if "." in resource else 'index.html'

    return await static_files.get_response(filename, request.scope)


root.include_router(websocket_ns)
api.include_router(tv_ns, prefix='/tv')
api.include_router(monitor_ns, prefix='/monitor')
api.include_router(health, prefix='/diagnostics')


def create_app() -> FastAPI:
    app = FastAPI(
        servers=[
            {
                "url": "{protocol}://localhost:5000/",
                "description": "Development",
                "variables": {
                    "protocol": {"enum": ["http", "https"], "default": "https"}
                },
            },
            {
                "url": "https://media-staging.herokuapps.com/",
                "description": "Staging",
            },
            {"url": "https://media.mause.me/", "description": "Production"},
        ],
        title='Media',
        version='0.1.0-' + (commit or 'dev'),
        debug=not production,
    )
    #    app.middleware_stack.generate_plain_text = generate_plain_text
    app.include_router(
        api,
        prefix='/api',
        dependencies=[security],
    )
    app.include_router(root, prefix='')

    origins = []
    if 'FRONTEND_DOMAIN' in os.environ:
        origins.append('https://' + os.environ['FRONTEND_DOMAIN'])

    if not production:
        origins.append('http://localhost:3000')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    simplify_operation_ids(app)

    return app
