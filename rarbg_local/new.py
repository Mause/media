import logging
import re
from asyncio import get_event_loop, new_event_loop, set_event_loop, sleep
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from functools import wraps
from itertools import chain
from queue import Empty, Queue
from threading import Event
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from unittest.mock import MagicMock
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from flask import _app_ctx_stack  # type: ignore
from flask import _request_ctx_stack  # type: ignore
from flask import Blueprint, Response, current_app, request
from flask.sessions import SecureCookieSessionInterface
from flask_login.utils import decode_cookie
from flask_user import UserManager, current_user
from flask_user.password_manager import PasswordManager
from flask_user.token_manager import TokenManager
from pydantic import BaseModel, Field
from requests.exceptions import HTTPError
from sqlalchemy import func

from .db import (
    Download,
    EpisodeDetails,
    Monitor,
    MonitorMediaType,
    MovieDetails,
    Role,
    Roles,
    User,
    db,
    get_movies,
    get_or_create,
)
from .health import health
from .models import (
    DownloadPost,
    EpisodeDetailsSchema,
    IndexResponse,
    MonitorGet,
    MonitorPost,
    MovieDetailsSchema,
    Orm,
    StatsResponse,
    TvSeasonResponse,
    UserShim,
    map_to,
)
from .providers import (
    PROVIDERS,
    FakeProvider,
    ProviderSource,
    search_for_movie,
    search_for_tv,
)
from .tmdb import (
    get_movie,
    get_movie_imdb_id,
    get_tv,
    get_tv_episodes,
    get_tv_imdb_id,
    search_themoviedb,
)
from .utils import non_null, precondition

app = FastAPI(
    servers=[
        {
            "url": "{protocol}://localhost:5000/api",
            "description": "Development",
            "variables": {"protocol": {"enum": ["http", "https"], "default": "https"}},
        },
        {"url": "https://media-staging.herokuapps.com/api", "description": "Staging"},
        {"url": "https://media.mause.me/api", "description": "Production"},
    ]
)


class FakeApp:
    import_name = __name__

    user_manager: UserManager

    def __init__(self, fastapi_app):
        self.debug = True
        self.config = {
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_ECHO': True,
            'SECRET_KEY': 'hkfircsc',
        }
        self.extensions = {}

    def teardown_appcontext(self, func):
        pass


def startup():
    fake_app = FakeApp(app)
    db.init_app(fake_app)
    db.app = fake_app

    engine = db.get_engine(fake_app, None)
    con = engine.raw_connection().connection
    con.create_collation("en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1)

    db.create_all()


fake = FakeApp(None)
fake.user_manager = UserManager(None, db, User)
verify_token = TokenManager(fake).verify_token
password_manager = PasswordManager(fake).password_crypt_context
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class MediaType(Enum):
    SERIES = 'series'
    MOVIE = 'movie'


class DownloadResponse(Orm):
    id: int


@app.get('/user/unauthorized')
def user():
    pass


@app.get('/delete/{type}/{id}')
async def delete(type: MediaType, id: int):
    query = db.session.query(
        EpisodeDetails if type == MediaType.SERIES else MovieDetails
    ).filter_by(id=id)
    precondition(query.count() > 0, 'Nothing to delete')
    query.delete()
    db.session.commit()

    return {}


@app.get('/redirect/plex/{tmdb_id}')
def redirect_plex():
    pass


@app.get('/redirect/{type_}/{ident}')
@app.get('/redirect/{type_}/{ident}/{season}/{episode}')
def redirect(type_: MediaType, ident: int, season: int = None, episode: int = None):
    pass


class EpisodeInfo(BaseModel):
    seasonnum: str
    epnum: str


class ITorrent(BaseModel):
    source: ProviderSource
    download: str
    seeders: int
    category: str
    title: str
    episode_info: EpisodeInfo


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


@app.get(
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

    return list(items)


class DownloadAllResponse(BaseModel):
    packs: List[ITorrent]
    complete: List[Tuple[str, List[ITorrent]]]
    incomplete: List[Tuple[str, List[ITorrent]]]


@app.get(
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


@app.get('/diagnostics')
def diagnostics():
    return health.run()[0]


@app.post(
    '/download', response_model=List[Union[MovieDetailsSchema, EpisodeDetailsSchema]]
)
async def download_post(
    things: List[DownloadPost],
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
                        if episode.episode_number == thing.episode
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
            )
        )

    db.session.commit()

    return results


@app.get('/index', response_model=IndexResponse)
async def index():
    from .main import resolve_series

    return IndexResponse(series=resolve_series(), movies=get_movies())


@app.get('/stats', response_model=List[StatsResponse])
async def stats():
    from .main import groupby

    keys = User.username, Download.type
    query = db.session.query(*keys, func.count(name='count')).group_by(*keys)

    return [
        {"user": user, 'values': {type: value for _, type, value in values}}
        for user, values in groupby(query, lambda row: row.username).items()
    ]


class MovieResponse(BaseModel):
    title: str
    imdb_id: str


@app.get('/movie/{tmdb_id:int}', response_model=MovieResponse)
def movie(tmdb_id: int):
    movie = get_movie(tmdb_id)
    return {"title": movie['title'], "imdb_id": movie['imdb_id']}


def magic(*args, **kwargs):
    # we ignore the arguments flask tries to give us
    rq = request._get_current_object()

    path = rq.path
    if path.startswith('/api'):
        path = '/' + path.split('/', 2)[-1]
    return call_sync(
        rq.method, path, urlencode(rq.args), headers=rq.headers, body=rq.data,
    )


def translate(path: str) -> str:
    return re.sub(r'\{([^}]*)\}', lambda m: '<' + m.group(1).split(':')[0] + '>', path)


class FakeBlueprint(Blueprint):
    def __init__(self):
        super().__init__('fastapi', __name__)

    def register(self, fapp, options, first_registration):
        state = self.make_setup_state(fapp, options, first_registration)
        for route in app.routes:
            state.add_url_rule(
                translate(route.path),
                view_func=magic,
                methods=getattr(route, 'methods', {'GET'}),
                endpoint=route,
            )


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


@app.get('/torrents', response_model=Dict[str, InnerTorrent])
async def torrents():
    from .main import get_keyed_torrents

    return get_keyed_torrents()


class SearchResponse(BaseModel):
    title: str
    type: MediaType
    year: int
    imdbID: int

    # deprecated
    Year: int = Field(deprecated=True)
    Type: MediaType = Field(deprecated=True)

    Config = map_to({'year': 'Year', 'type': 'Type'})


@app.get('/search', response_model=List[SearchResponse])
async def search(query: str):
    # dirty hack to make aliasing work
    return [type('SearchResponse', (), v)() for v in search_themoviedb(query)]


monitor_ns = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str


@app.post('/create_user', response_model=UserShim, tags=['user'])
def create_user(item: UserCreate):
    user = User(username=item.username, password=password_manager.hash(item.password),)
    db.session.add(user)
    db.session.commit()

    return user


async def get_current_user(
    remember_token: str = Cookie(None), session: str = Cookie(None)
) -> Optional[User]:
    if session:
        request = MagicMock(cookies={'session': session})
        sess = SecureCookieSessionInterface().open_session(current_app, request)
        user_id = sess['_user_id']
        user_id, _ = verify_token(user_id)
        return db.session.query(User).get(user_id)

    try:
        return current_user._get_current_object()
    except Exception:
        pass

    user = None
    if remember_token:
        user_id = decode_cookie(remember_token)

        user = db.session.query(User).filter_by(username=user_id).one_or_none()

    if user:
        return user
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


class PromoteCreate(BaseModel):
    username: str
    roles: List[str]


@app.post('/promote', tags=['user'])
def promote(req: PromoteCreate, calling_user: User = Depends(get_current_user)):
    if Roles.Admin not in calling_user.roles:
        raise HTTPException(403, 'Insufficient caller rights')

    user = db.session.query(User).filter_by(username=req.username).one_or_none()
    if user:
        user.roles = [get_or_create(Role, name=role) for role in req.roles]
        db.session.commit()
    else:
        raise HTTPException(422, "User does not exist")


@monitor_ns.get('', tags=['monitor'], response_model=List[MonitorGet])
async def monitor_get(user: User = Depends(get_current_user)):
    return db.session.query(Monitor).all()


@monitor_ns.delete('/{monitor_id}', tags=['monitor'])
async def monitor_delete(monitor_id: int):
    query = db.session.query(Monitor).filter_by(id=monitor_id)
    precondition(query.count() > 0, 'Nothing to delete')
    query.delete()
    db.session.commit()
    return {}


@app.post("/token", tags=['user'])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.session.query(User).filter_by(username=form_data.username).one_or_none()

    if password_manager.verify(form_data.password, user.password if user else None):
        return {"access_token": user.username, "token_type": "bearer"}

    raise HTTPException(status_code=400, detail="Incorrect username or password")


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
async def monitor_post(monitor: MonitorPost, user: User = Depends(get_current_user)):
    media = validate_id(monitor.type, monitor.tmdb_id)
    c = (
        db.session.query(Monitor)
        .filter_by(tmdb_id=monitor.tmdb_id, type=monitor.type)
        .one_or_none()
    )
    if not c:
        c = Monitor(
            tmdb_id=monitor.tmdb_id, added_by=user, type=monitor.type, title=media
        )
        db.session.add(c)
        db.session.commit()
    return c


tv_ns = APIRouter()


class SeasonMeta(BaseModel):
    episode_count: int
    season_number: int


class TvResponse(BaseModel):
    number_of_seasons: int
    title: str
    imdb_id: str
    seasons: List[SeasonMeta]


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


@app.websocket("/ws")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()

    request = await websocket.receive_json()

    for item in _stream(**request):
        await websocket.send_json(item)


app.include_router(tv_ns, prefix='/tv')
app.include_router(monitor_ns, prefix='/monitor')


executor = ThreadPoolExecutor(10)


def call_sync(method='GET', path='/monitor', query_string='', headers=None, body=None):
    response: Dict[str, Any] = {}

    async def send(message):
        type_ = message['type']
        logging.info('received message of type %s', type_)

        if type_ == 'http.response.start':
            response.update(message)
            first_event.set()
        elif type_ == 'http.response.body':
            body = message.pop('body', None)
            if body:
                body_queue.put(body)

            if 'more_body' in message:
                if not message['more_body']:
                    last_event.set()
            else:
                last_event.set()
        else:
            raise Exception('unknown message type: ' + type_)

    async def recieve():
        if body:
            return {'type': 'http.request', 'body': body}
        elif last_event.is_set():
            return {'type': 'http.disconnect'}
        else:
            await sleep(0)
            return {'type': 'http.*'}

    async def call():

        headerz = [
            (key.encode().lower(), value.encode()) for key, value in list(headers or [])
        ]
        await app(
            {
                'type': 'http',
                'path': path,
                'method': method,
                'query_string': query_string,
                'headers': headerz,
            },
            recieve,
            send,
        )

    rq = _request_ctx_stack.top
    appc = _app_ctx_stack.top

    def worker():
        _request_ctx_stack.push(rq)
        _app_ctx_stack.push(appc)
        try:
            el = get_event_loop()
        except RuntimeError:
            el = new_event_loop()
            set_event_loop(el)
        el.run_until_complete(call())

    first_event = Event()
    last_event = Event()
    body_queue: Queue[Dict] = Queue()

    def genny():
        while not last_event.is_set():
            try:
                yield body_queue.get_nowait()
            except Empty:
                pass
        while not body_queue.empty():
            yield body_queue.get()

    response['response'] = genny()

    executor.submit(worker)
    first_event.wait()  # wait until we have the status, headers

    response.pop('type')
    response['headers'] = dict(response['headers'])
    response['mimetype'] = response['headers'].pop(b'content-type').decode()

    return Response(**response)


if __name__ == "__main__":
    print(call_sync())
