import logging
import os
import traceback
from collections import ChainMap
from collections.abc import AsyncGenerator, Callable
from functools import wraps
from typing import (
    Annotated,
    Literal,
    TypeVar,
    Union,
)
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Security, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.security import (
    SecurityScopes,
)
from fastapi_utils.openapi import simplify_operation_ids
from pydantic import BaseModel, SecretStr, ValidationError
from requests.exceptions import HTTPError
from sqlalchemy import func
from sqlalchemy.orm.session import Session
from starlette.staticfiles import StaticFiles

from .auth import auth_hook, get_my_jwkaas
from .db import (
    Download,
    EpisodeDetails,
    Monitor,
    MonitorMediaType,
    MovieDetails,
    User,
    get_db,
    get_movies,
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
    MonitorGet,
    MonitorPost,
    MovieDetailsSchema,
    MovieResponse,
    ProviderSource,
    SearchResponse,
    StatsResponse,
    TvResponse,
    TvSeasonResponse,
)
from .plex import get_imdb_in_plex, get_plex
from .providers import (
    get_providers,
    search_for_movie,
    search_for_tv,
)
from .providers.abc import (
    MovieProvider,
    TvProvider,
)
from .settings import Settings, get_settings
from .singleton import get, singleton
from .tmdb import (
    get_json,
    get_movie,
    get_movie_imdb_id,
    get_tv,
    get_tv_episodes,
    get_tv_imdb_id,
    search_themoviedb,
)
from .types import ImdbId, TmdbId
from .utils import Message, non_null, precondition

api = APIRouter()
logger = logging.getLogger(__name__)
logging.getLogger('backoff').handlers.clear()
T = TypeVar('T')


def generate_plain_text(exc):
    logger.exception('Error occured', exc_info=exc)
    return ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))


async def get_current_user(
    security_scopes: SecurityScopes,
    session=Depends(get_db),
    token_info=Depends(get_my_jwkaas),
):
    user = auth_hook(
        session=session, security_scopes=security_scopes, token_info=token_info
    )
    if user:
        return user
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


security = Security(
    get_current_user,
    scopes=['openid'],
)


@api.get('/user/unauthorized')
def user():
    pass


def safe_delete(session: Session, entity: type[T], id: int):
    query = session.query(entity).filter_by(id=id)
    precondition(query.count() > 0, 'Nothing to delete')
    query.delete()
    session.commit()


@api.get('/delete/{type}/{id}')
async def delete(type: MediaType, id: int, session: Session = Depends(get_db)):
    safe_delete(
        session, EpisodeDetails if type == MediaType.SERIES else MovieDetails, id
    )

    return {}


def eventstream(func: Callable[..., AsyncGenerator[BaseModel, None]]):
    @wraps(func)
    async def decorator(*args, **kwargs):
        async def internal() -> AsyncGenerator[str, None]:
            async for rset in func(*args, **kwargs):
                yield f'data: {rset.model_dump_json()}\n\n'
            yield 'data:\n\n'

        return StreamingResponse(
            internal(),
            media_type="text/event-stream",
        )

    return decorator


StreamType = Literal['series', 'movie']


@api.get(
    '/stream/{type}/{tmdb_id}',
    response_class=StreamingResponse,
    responses={200: {"model": ITorrent, "content": {'text/event-stream': {}}}},
)
@eventstream
async def stream(
    type: StreamType,
    tmdb_id: TmdbId,
    source: ProviderSource,
    season: int | None = None,
    episode: int | None = None,
):
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
    '/select/{tmdb_id}/season/{season}/download_all', response_model=DownloadAllResponse
)
async def select(tmdb_id: TmdbId, season: int):
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

    return {
        'packs': packs,
        'complete': complete_or_not.get(True, []),
        'incomplete': complete_or_not.get(False, []),
    }


@api.post(
    '/download', response_model=list[Union[MovieDetailsSchema, EpisodeDetailsSchema]]
)
async def download_post(
    things: list[DownloadPost],
    added_by: Annotated[User, security],
    session: Session = Depends(get_db),
) -> list[MovieDetails | EpisodeDetails]:
    results: list[MovieDetails | EpisodeDetails] = []

    # work around a fastapi bug
    # see for more details https://github.com/fastapi/fastapi/discussions/6024
    session = non_null(session.object_session(added_by))

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
            add_single(
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
    session.commit()

    return results


@api.get('/index', response_model=IndexResponse)
async def index(session: Session = Depends(get_db)):
    return IndexResponse(
        series=await resolve_series(session), movies=get_movies(session)
    )


@api.get('/stats', response_model=list[StatsResponse])
async def stats(session: Session = Depends(get_db)):
    def process(added_by_id: int, values):
        user = session.get(User, added_by_id)
        if not user:
            return None

        return {
            "user": user.username,
            "values": {type.lower(): value for _, type, value in values},
        }

    keys = Download.added_by_id, Download.type
    query = session.query(*keys, func.count(name='count')).group_by(*keys)

    return [
        process(added_by_id, values)
        for added_by_id, values in groupby(query, lambda row: row.added_by_id).items()
    ]


@api.get('/movie/{tmdb_id:int}', response_model=MovieResponse)
async def movie(tmdb_id: TmdbId):
    return await get_movie(tmdb_id)


@api.get('/torrents', response_model=dict[str, InnerTorrent])
async def torrents():
    return get_keyed_torrents()


@api.get('/search', response_model=list[SearchResponse])
async def search(query: str):
    return await search_themoviedb(query)


monitor_ns = APIRouter(tags=['monitor'])


@monitor_ns.get('', response_model=list[MonitorGet])
async def monitor_get(
    user: Annotated[User, security], session: Session = Depends(get_db)
):
    return session.query(Monitor).all()


@monitor_ns.delete('/{monitor_id}')
async def monitor_delete(monitor_id: int, session: Session = Depends(get_db)):
    safe_delete(session, Monitor, monitor_id)

    return {}


async def validate_id(type: MonitorMediaType, tmdb_id: TmdbId) -> str:
    try:
        return (
            (await get_movie(tmdb_id)).title
            if type == MonitorMediaType.MOVIE
            else (await get_tv(tmdb_id)).name
        )
    except HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(422, f'{type.name} not found: {tmdb_id}')
        else:
            raise


@monitor_ns.post('', response_model=MonitorGet, status_code=201)
async def monitor_post(
    monitor: MonitorPost,
    user: Annotated[User, security],
    session: Session = Depends(get_db),
):
    media = await validate_id(monitor.type, monitor.tmdb_id)
    c = (
        session.query(Monitor)
        .filter_by(tmdb_id=monitor.tmdb_id, type=monitor.type)
        .one_or_none()
    )
    if not c:
        c = Monitor(
            tmdb_id=monitor.tmdb_id, added_by=user, type=monitor.type, title=media
        )
        session.add(c)
        session.commit()
    return c


tv_ns = APIRouter(tags=['tv'])


@tv_ns.get('/{tmdb_id}', response_model=TvResponse)
async def api_tv(tmdb_id: TmdbId):
    tv = await get_tv(tmdb_id)
    return TvResponse(
        **tv.model_dump(), imdb_id=await get_tv_imdb_id(tmdb_id), title=tv.name
    )


@tv_ns.get('/{tmdb_id}/season/{season}', response_model=TvSeasonResponse)
async def api_tv_season(tmdb_id: TmdbId, season: int):
    return await get_tv_episodes(tmdb_id, season)


class StreamArgs(BaseModel):
    authorization: SecretStr

    type: StreamType
    tmdb_id: TmdbId
    season: int | None = None
    episode: int | None = None


async def _stream(
    type: str,
    tmdb_id: TmdbId,
    season: int | None = None,
    episode: int | None = None,
):
    if type == 'series':
        tasks, queue = await search_for_tv(
            await get_tv_imdb_id(tmdb_id), tmdb_id, non_null(season), episode
        )
    else:
        tasks, queue = await search_for_movie(await get_movie_imdb_id(tmdb_id), tmdb_id)

    while not all(task.done() for task in tasks):
        item = await queue.get()
        if isinstance(item, Message):
            logger.info('Message from provider: %s', item)
        else:
            yield item.model_dump(mode='json')


root = APIRouter()


@root.websocket("/ws")
async def websocket_stream(websocket: WebSocket):
    def fake(user: Annotated[User, security]):
        return user

    logger.info('Got websocket connection')
    await websocket.accept()

    try:
        request = StreamArgs.model_validate(await websocket.receive_json())
    except ValidationError as e:
        await websocket.send_json(
            {'error': str(e), 'type': type(e).__name__, 'errors': e.errors()}
        )
        await websocket.close()
        return
    logger.info('Got request: %s', request)

    try:
        user = await get(
            websocket.app,
            fake,
            Request(
                scope=ChainMap(
                    {
                        'type': 'http',
                        'headers': [
                            (
                                b"authorization",
                                (request.authorization.get_secret_value()).encode(),
                            ),
                        ],
                    },
                    websocket.scope,
                ),
                receive=websocket.receive,
                send=websocket.send,
            ),
        )
    except Exception as e:
        logger.exception('Unable to authenticate websocket request')
        await websocket.send_json({'error': str(e), 'type': type(e).__name__})
        await websocket.close()
        raise

    logger.info('Authed user: %s', user)

    async for item in _stream(
        type=request.type,
        tmdb_id=request.tmdb_id,
        season=request.season,
        episode=request.episode,
    ):
        await websocket.send_json(item)

    logger.info('Finished streaming')
    await websocket.close()


@singleton
def get_static_files(settings: Settings = Depends(get_settings)):
    return StaticFiles(directory=str(settings.static_resources_path))


@root.get('/redirect/plex/{imdb_id}')
def redirect_to_plex(imdb_id: ImdbId, plex=Depends(get_plex)):
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
):
    if type_ == 'movie':
        imdb_id = await get_movie_imdb_id(tmdb_id)
    elif season:
        imdb_id = (
            await get_json(
                f'tv/{tmdb_id}/season/{season}/episode/{episode}/external_ids'
            )
        )['imdb_id']
    else:
        imdb_id = await get_tv_imdb_id(tmdb_id)

    return RedirectResponse(f'https://www.imdb.com/title/{imdb_id}')


@root.api_route('/{resource:path}', methods=['GET', 'HEAD'], include_in_schema=False)
@root.api_route('/', methods=['GET', 'HEAD'], include_in_schema=False)
async def static(
    request: Request,
    resource: str = '',
    static_files: StaticFiles = Depends(get_static_files),
):
    filename = resource if "." in resource else 'index.html'

    return await static_files.get_response(filename, request.scope)


api.include_router(tv_ns, prefix='/tv')
api.include_router(monitor_ns, prefix='/monitor')
api.include_router(health, prefix='/diagnostics')


def create_app():
    keys = ['HEROKU_SLUG_COMMIT', 'RAILWAY_GIT_COMMIT_SHA']
    value = next((os.environ[key] for key in keys if key in os.environ), None)

    app = FastAPI(
        servers=[
            {
                "url": "{protocol}://localhost:5000/",
                "description": "Development",
                "variables": {
                    "protocol": {"enum": ["http", "https"], "default": "https"}
                },
            },
            {"url": "https://media-staging.herokuapps.com/", "description": "Staging"},
            {"url": "https://media.mause.me/", "description": "Production"},
        ],
        title='Media',
        version='0.1.0-' + (value or 'dev'),
        debug=not ('HEROKU' in os.environ or 'RAILWAY_ENVIRONMENT_NAME' in os.environ),
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

    on_heroku = 'HEROKU' in os.environ
    production = os.environ.get('RAILWAY_ENVIRONMENT_NAME') == 'production' or on_heroku
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
