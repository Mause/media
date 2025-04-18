import logging
import os
import traceback
from functools import wraps
from os import getpid
from pathlib import Path
from typing import AsyncGenerator, Callable, Dict, List, Optional, Type, Union
from urllib.parse import urlencode

import backoff
import psycopg2
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Security, WebSocket
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OpenIdConnect,
    SecurityScopes,
)
from fastapi_utils.openapi import simplify_operation_ids
from plexapi.media import Media
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from pydantic import BaseModel, BaseSettings, SecretStr
from requests.exceptions import HTTPError
from sqlalchemy import create_engine, event, func
from sqlalchemy.orm import sessionmaker
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
    get_movies,
)
from .health import health
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
    SearchResponse,
    StatsResponse,
    TvResponse,
    TvSeasonResponse,
)
from .providers import PROVIDERS, ProviderSource, search_for_movie, search_for_tv
from .singleton import singleton
from .tmdb import (
    get_json,
    get_movie,
    get_movie_imdb_id,
    get_tv,
    get_tv_episodes,
    get_tv_imdb_id,
    search_themoviedb,
)
from .utils import non_null, precondition

api = APIRouter()


def generate_plain_text(exc):
    logging.exception('Error occured', exc_info=exc)
    return ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))


class XOpenIdConnect(OpenIdConnect):
    async def __call__(  # type: ignore[override]
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        return await HTTPBearer().__call__(request)


openid_connect = XOpenIdConnect(
    openIdConnectUrl='https://mause.au.auth0.com/.well-known/openid-configuration'
)


class Settings(BaseSettings):
    root = Path(__file__).parent.parent.absolute()
    database_url = f"sqlite:///{root}/db.db"
    static_resources_path = root / 'app/build'
    plex_username: Optional[str] = None
    plex_password: Optional[SecretStr] = None


@singleton
async def get_settings():
    return Settings()


@singleton
def get_session_local(settings: Settings = Depends(get_settings)):
    db_url = settings.database_url
    logging.info('db_url: %s', db_url)

    sqlite = 'sqlite' in db_url

    ca = {"check_same_thread": False} if sqlite else {}
    engine_args = (
        {} if sqlite else {'max_overflow': 10, 'pool_size': 5, 'pool_recycle': 300}
    )
    engine = create_engine(db_url, connect_args=ca, **engine_args, echo_pool='debug')

    if sqlite:

        @event.listens_for(engine, 'connect')
        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.create_collation(
                "en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1
            )
            dbapi_con.execute('pragma foreign_keys=ON')

    else:

        @event.listens_for(engine, "do_connect")
        @backoff.on_exception(
            backoff.fibo,
            psycopg2.OperationalError,
            max_tries=5,
            giveup=lambda e: "too many connections for role" not in e.args[0],
        )
        def receive_do_connect(dialect, conn_rec, cargs, cparams):
            return psycopg2.connect(*cargs, **cparams)

    return sessionmaker(autocommit=False, autoflush=True, bind=engine)


@api.get('/diagnostics/pool')
def pool(sessionlocal=Depends(get_session_local)):
    def get(field):
        value = getattr(pool, field, None)

        return value() if callable(value) else value

    pool = sessionlocal.kw['bind'].pool
    return {
        'worker_id': getpid(),
        'size': get('size'),
        'checkedin': get('checkedin'),
        'overflow': get('overflow'),
        'checkedout': get('checkedout'),
    }


def get_db(session_local=Depends(get_session_local)):
    sl = session_local()
    try:
        yield sl
    finally:
        sl.close()


async def get_current_user(
    security_scopes: SecurityScopes,
    session=Depends(get_db),
    header=Depends(openid_connect),
    jwkaas=Depends(get_my_jwkaas),
):
    user = auth_hook(
        session=session, header=header, security_scopes=security_scopes, jwkaas=jwkaas
    )
    if user:
        return user
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


@api.get('/user/unauthorized')
def user():
    pass


def safe_delete(session: Session, entity: Type, id: int):
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
                yield f'data: {rset.json()}\n\n'
            yield 'data:\n\n'

        return StreamingResponse(
            internal(),
            media_type="text/event-stream",
        )

    return decorator


@api.get(
    '/stream/{type}/{tmdb_id}',
    response_class=StreamingResponse,
    responses={200: {"model": ITorrent, "content": {'text/event-stream': {}}}},
)
@eventstream
async def stream(
    type: str,
    tmdb_id: str,
    source: ProviderSource,
    season: Optional[int] = None,
    episode: Optional[int] = None,
) -> AsyncGenerator[BaseModel, None]:
    provider = next(
        (provider for provider in PROVIDERS if provider.name == source.value),
        None,
    )
    if not provider:
        raise HTTPException(422, 'Invalid provider')

    if type == 'series':
        async for item in provider.search_for_tv(
            await get_tv_imdb_id(tmdb_id), int(tmdb_id), non_null(season), episode
        ):
            yield item
    else:
        async for item in provider.search_for_movie(
            await get_movie_imdb_id(tmdb_id), int(tmdb_id)
        ):
            yield item


@api.get(
    '/select/{tmdb_id}/season/{season}/download_all', response_model=DownloadAllResponse
)
async def select(tmdb_id: int, season: int):

    results = search_for_tv(await get_tv_imdb_id(tmdb_id), int(tmdb_id), int(season))

    episodes = get_tv_episodes(tmdb_id, season).episodes

    packs_or_not = groupby(
        results, lambda result: extract_marker(result.title)[1] is None
    )
    packs = sorted(
        packs_or_not.get(True, []), key=lambda result: result.seeders, reverse=True
    )

    grouped_results = groupby(
        packs_or_not.get(False, []), lambda result: normalise(episodes, result.title)
    )
    complete_or_not = groupby(
        grouped_results.items(), lambda rset: len(rset[1]) == len(episodes)
    )

    return dict(
        packs=packs,
        complete=complete_or_not.get(True, []),
        incomplete=complete_or_not.get(False, []),
    )


@api.get('/diagnostics')
def diagnostics():
    return health.run()[0]


@api.post(
    '/download', response_model=List[Union[MovieDetailsSchema, EpisodeDetailsSchema]]
)
async def download_post(
    things: List[DownloadPost],
    added_by: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> List[Union[MovieDetails, EpisodeDetails]]:

    results: List[Union[MovieDetails, EpisodeDetails]] = []

    for thing in things:
        is_tv = thing.season is not None

        show_title: Optional[str]
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
                        if str(episode.episode_number) == thing.episode
                    ),
                    None,
                )
                assert episode, f'Could not find episode: {thing}'
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
                    await get_tv_imdb_id(str(thing.tmdb_id))
                    if is_tv
                    else await get_movie_imdb_id(str(thing.tmdb_id))
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

    return IndexResponse(series=resolve_series(session), movies=get_movies(session))


@api.get('/stats', response_model=List[StatsResponse])
async def stats(session: Session = Depends(get_db)):

    keys = Download.added_by_id, Download.type
    query = session.query(*keys, func.count(name='count')).group_by(*keys)

    return [
        {
            "user": session.query(User).get(added_by_id).username,
            "values": {type.lower(): value for _, type, value in values},
        }
        for added_by_id, values in groupby(query, lambda row: row.added_by_id).items()
    ]


@api.get('/movie/{tmdb_id:int}', response_model=MovieResponse)
async def movie(tmdb_id: int):
    return await get_movie(tmdb_id)


@api.get('/torrents', response_model=Dict[str, InnerTorrent])
async def torrents():

    return get_keyed_torrents()


@api.get('/search', response_model=List[SearchResponse])
async def search(query: str):
    return await search_themoviedb(query)


monitor_ns = APIRouter()


@monitor_ns.get('', tags=['monitor'], response_model=List[MonitorGet])
async def monitor_get(
    user: User = Depends(get_current_user), session: Session = Depends(get_db)
):
    return session.query(Monitor).all()


@monitor_ns.delete('/{monitor_id}', tags=['monitor'])
async def monitor_delete(monitor_id: int, session: Session = Depends(get_db)):
    safe_delete(session, Monitor, monitor_id)

    return {}


async def validate_id(type: MonitorMediaType, tmdb_id: int) -> str:
    try:
        return (
            (await get_movie(tmdb_id)).title
            if type == MonitorMediaType.MOVIE
            else get_tv(tmdb_id).name
        )
    except HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(422, f'{type.name} not found: {tmdb_id}')
        else:
            raise


@monitor_ns.post('', tags=['monitor'], response_model=MonitorGet, status_code=201)
async def monitor_post(
    monitor: MonitorPost,
    user: User = Depends(get_current_user),
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


tv_ns = APIRouter()


@tv_ns.get('/{tmdb_id}', tags=['tv'], response_model=TvResponse)
async def api_tv(tmdb_id: int):
    tv = await get_tv(tmdb_id)
    return TvResponse(**tv.dict(), imdb_id=await get_tv_imdb_id(tmdb_id), title=tv.name)


@tv_ns.get('/{tmdb_id}/season/{season}', tags=['tv'], response_model=TvSeasonResponse)
async def api_tv_season(tmdb_id: int, season: int):
    return await get_tv_episodes(tmdb_id, season)


async def _stream(type: str, tmdb_id: str, season=None, episode=None):
    if type == 'series':
        items = search_for_tv(
            await get_tv_imdb_id(tmdb_id), int(tmdb_id), season, episode
        )
    else:
        items = search_for_movie(await get_movie_imdb_id(tmdb_id), int(tmdb_id))

    return (item.dict() for item in items)


@api.websocket("/ws")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()

    request = await websocket.receive_json()

    for item in await _stream(**request):
        await websocket.send_json(item)


root = APIRouter()


@singleton
def get_static_files(settings: Settings = Depends(get_settings)):
    return StaticFiles(directory=str(settings.static_resources_path))


@singleton
def get_plex(settings=Depends(get_settings)) -> PlexServer:
    acct = MyPlexAccount(settings.plex_username, settings.plex_password)
    novell = acct.resource('Novell')
    novell.connections = [c for c in novell.connections if not c.local]
    return novell.connect(ssl=True)


def get_imdb_in_plex(imdb_id: str, plex) -> Optional[Media]:
    guid = f"com.plexapp.agents.imdb://{imdb_id}?lang=en"
    items = plex.library.search(guid=guid)
    return items[0] if items else None


@root.get('/redirect/plex/{tmdb_id}')
def redirect_to_plex(tmdb_id: str, plex=Depends(get_plex)):
    dat = get_imdb_in_plex(tmdb_id, plex)
    if not dat:
        raise HTTPException(404, 'Not found in plex')

    server_id = plex.machineIdentifier

    return RedirectResponse(
        f'https://app.plex.tv/desktop#!/server/{server_id}/details?'
        + urlencode({'key': f'/library/metadata/{dat.ratingKey}'})
    )


@root.get('/redirect/{type_}/{tmdb_id}')
@root.get('/redirect/{type_}/{tmdb_id}/{season}/{episode}')
async def redirect_to_imdb(
    type_: MediaType,
    tmdb_id: int,
    season: Optional[int] = None,
    episode: Optional[int] = None,
):
    if type_ == 'movie':
        imdb_id = await get_movie_imdb_id(tmdb_id)
    elif season:
        imdb_id = get_json(
            f'tv/{tmdb_id}/season/{season}/episode/{episode}/external_ids'
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


def create_app():
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
        version='0.1.0-' + os.environ.get('HEROKU_SLUG_COMMIT', 'dev'),
        debug='HEROKU' not in os.environ,
    )
    app.middleware_stack.generate_plain_text = generate_plain_text
    app.include_router(
        api,
        prefix='/api',
        dependencies=[Security(get_current_user, scopes=['openid'])],
    )
    app.include_router(root, prefix='')
    simplify_operation_ids(app)

    return app
