import logging
import os
import re
import traceback
from functools import wraps
from itertools import chain
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Security, WebSocket
from fastapi.requests import Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OpenIdConnect,
    SecurityScopes,
)
from flask import safe_join
from pydantic import BaseModel, BaseSettings
from requests.exceptions import HTTPError
from sqlalchemy import create_engine, event, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

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
from .providers import (
    PROVIDERS,
    FakeProvider,
    ProviderSource,
    search_for_movie,
    search_for_tv,
)
from .singleton import get, singleton
from .tmdb import (
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
    async def __call__(
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


@singleton
async def get_settings():
    return Settings()


@singleton
def get_session_local(settings: Settings = Depends(get_settings)):
    db_url = settings.database_url
    logging.info('db_url: %s', db_url)
    ca = {"check_same_thread": False} if 'sqlite' in db_url else {}
    engine = create_engine(db_url, connect_args=ca)
    if 'sqlite' in db_url:

        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.create_collation(
                "en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1
            )
            dbapi_con.execute('pragma foreign_keys=ON')

        event.listen(engine, 'connect', _fk_pragma_on_connect)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_db(session_local=Depends(get_session_local)):
    return session_local()


async def get_current_user(
    security_scopes: SecurityScopes,
    session=Depends(get_db),
    header=Security(openid_connect),
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


@api.get('/delete/{type}/{id}')
async def delete(type: MediaType, id: int, session: Session = Depends(get_db)):
    query = session.query(
        EpisodeDetails if type == MediaType.SERIES else MovieDetails
    ).filter_by(id=id)
    precondition(query.count() > 0, 'Nothing to delete')
    query.delete()
    session.commit()

    return {}


@api.get('/redirect/plex/{tmdb_id}')
def redirect_plex():
    pass


@api.get('/redirect/{type_}/{ident}')
@api.get('/redirect/{type_}/{ident}/{season}/{episode}')
def redirect(type_: MediaType, ident: int, season: int = None, episode: int = None):
    pass


def eventstream(func: Callable[..., Iterable[BaseModel]]):
    @wraps(func)
    async def decorator(*args, **kwargs):
        sr = StreamingResponse(
            chain(
                (f'data: {rset.json()}\n\n' for rset in func(*args, **kwargs)),
                ['data:\n\n'],
            ),
            media_type="text/event-stream",
        )
        return sr

    return decorator


@api.get(
    '/stream/{type}/{tmdb_id}',
    response_class=StreamingResponse,
    responses={200: {"model": ITorrent, "content": {'text/event-stream': {}}}},
)
@eventstream
def stream(
    type: str,
    tmdb_id: str,
    source: ProviderSource = None,
    season: int = None,
    episode: int = None,
):
    if source:
        provider = next(
            (provider for provider in PROVIDERS if provider.name == source.value), None,
        )
        if not provider:
            raise HTTPException(422, 'Invalid provider')
    else:
        provider = FakeProvider()

    if type == 'series':
        items = provider.search_for_tv(
            get_tv_imdb_id(tmdb_id), int(tmdb_id), non_null(season), episode
        )
    else:
        items = provider.search_for_movie(get_movie_imdb_id(tmdb_id), int(tmdb_id))

    return items


@api.get(
    '/select/{tmdb_id}/season/{season}/download_all', response_model=DownloadAllResponse
)
async def select(tmdb_id: int, season: int):
    from .main import extract_marker, groupby, normalise

    results = search_for_tv(get_tv_imdb_id(tmdb_id), int(tmdb_id), int(season))

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
    from .main import add_single

    results: List[Union[MovieDetails, EpisodeDetails]] = []

    for thing in things:
        is_tv = thing.season is not None

        item = get_tv(thing.tmdb_id) if is_tv else get_movie(thing.tmdb_id)
        if is_tv:
            subpath = f'tv_shows/{item["name"]}/Season {thing.season}'
        else:
            subpath = 'movies'

        show_title = None
        if thing.season is not None:
            if thing.episode is None:
                title = f'Season {thing.season}'
            else:
                episodes = get_tv_episodes(thing.tmdb_id, thing.season).episodes
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

            show_title = item['name']
        else:
            title = item['title']

        results.append(
            add_single(
                session=session,
                magnet=thing.magnet,
                imdb_id=(
                    get_tv_imdb_id(str(thing.tmdb_id))
                    if is_tv
                    else get_movie_imdb_id(str(thing.tmdb_id))
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
    from .main import resolve_series

    return IndexResponse(series=resolve_series(session), movies=get_movies(session))


@api.get('/stats', response_model=List[StatsResponse])
async def stats(session: Session = Depends(get_db)):
    from .main import groupby

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
def movie(tmdb_id: int):
    movie = get_movie(tmdb_id)
    return {"title": movie['title'], "imdb_id": movie['imdb_id']}


def translate(path: str) -> str:
    return re.sub(r'\{([^}]*)\}', lambda m: '<' + m.group(1).split(':')[0] + '>', path)


@api.get('/torrents', response_model=Dict[str, InnerTorrent])
async def torrents():
    from .main import get_keyed_torrents

    return get_keyed_torrents()


@api.get('/search', response_model=List[SearchResponse])
async def search(query: str):
    # dirty hack to make aliasing work
    return [type('SearchResponse', (), v)() for v in search_themoviedb(query)]


monitor_ns = APIRouter()


@monitor_ns.get('', tags=['monitor'], response_model=List[MonitorGet])
async def monitor_get(
    user: User = Depends(get_current_user), session: Session = Depends(get_db)
):
    return session.query(Monitor).all()


@monitor_ns.delete('/{monitor_id}', tags=['monitor'])
async def monitor_delete(monitor_id: int, session: Session = Depends(get_db)):
    query = session.query(Monitor).filter_by(id=monitor_id)
    precondition(query.count() > 0, 'Nothing to delete')
    query.delete()
    session.commit()
    return {}


def validate_id(type: MonitorMediaType, tmdb_id: int) -> str:
    try:
        return (
            get_movie(tmdb_id)['title']
            if type == MonitorMediaType.MOVIE
            else get_tv(tmdb_id)['name']
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
    media = validate_id(monitor.type, monitor.tmdb_id)
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
def api_tv(tmdb_id: int):
    tv = get_tv(tmdb_id)
    return {**tv, 'imdb_id': get_tv_imdb_id(tmdb_id), 'title': tv['name']}


@tv_ns.get('/{tmdb_id}/season/{season}', tags=['tv'], response_model=TvSeasonResponse)
def api_tv_season(tmdb_id: int, season: int):
    return get_tv_episodes(tmdb_id, season)


def _stream(type: str, tmdb_id: str, season=None, episode=None):
    if type == 'series':
        items = search_for_tv(get_tv_imdb_id(tmdb_id), int(tmdb_id), season, episode)
    else:
        items = search_for_movie(get_movie_imdb_id(tmdb_id), int(tmdb_id))

    return (item.dict() for item in items)


@api.websocket("/ws")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()

    request = await websocket.receive_json()

    for item in _stream(**request):
        await websocket.send_json(item)


root = APIRouter()


@root.get('/{resource:path}', include_in_schema=False)
@root.get('/', include_in_schema=False)
async def static(resource: str = '', settings: Settings = Depends(get_settings)):
    filename = resource if "." in resource else 'index.html'

    return FileResponse(path=safe_join(settings.static_resources_path, filename))


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def auth(self, user=Depends(get_current_user)):
        ...

    async def __call__(self, scope, recieve, send):
        if scope['type'] != 'lifespan':
            request = Request(scope, recieve, send)
            if request.url.path.startswith('/api'):
                await get(request.app, self.auth, request)

        await self.app(scope, recieve, send)


api.include_router(tv_ns, prefix='/tv')
api.include_router(monitor_ns, prefix='/monitor')


def create_app():
    app = FastAPI(
        servers=[
            {
                "url": "{protocol}://localhost:5000/api",
                "description": "Development",
                "variables": {
                    "protocol": {"enum": ["http", "https"], "default": "https"}
                },
            },
            {
                "url": "https://media-staging.herokuapps.com/api",
                "description": "Staging",
            },
            {"url": "https://media.mause.me/api", "description": "Production"},
        ],
        debug='HEROKU' not in os.environ,
    )
    app.middleware_stack.generate_plain_text = generate_plain_text
    app.include_router(api, prefix='/api')
    app.include_router(root, prefix='')

    app.add_middleware(AuthMiddleware)

    return app
