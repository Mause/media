import re
from asyncio import get_event_loop
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

from fastapi import APIRouter, Cookie, Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from flask import Response, current_app
from flask.sessions import SecureCookieSessionInterface
from flask_login.utils import decode_cookie
from flask_user import UserManager, current_user
from flask_user.password_manager import PasswordManager
from flask_user.token_manager import TokenManager
from pydantic import BaseModel, validator
from pydantic.utils import GetterDict

from .db import MediaType as FMediaType
from .db import Monitor, Role, Roles, User, db, get_or_create
from .models import Orm, map_to
from .providers import ProviderSource
from .tmdb import get_movie, get_tv, get_tv_episodes, get_tv_imdb_id
from .utils import precondition

app = FastAPI()


class FakeApp:
    import_name = __name__

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


app.user_manager = UserManager(None, db, User)
verify_token = TokenManager(FakeApp(None)).verify_token
password_manager = PasswordManager(app).password_crypt_context
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class MediaType(Enum):
    SERIES = 'series'
    MOVIE = 'movie'


class DownloadResponse(Orm):
    id: int


@app.get('/user/unauthorized')
def user():
    pass


@app.get('/delete/<type>/<id>')
def delete(type: MediaType, id: int):
    pass


@app.get('/redirect/plex/<tmdb_id>')
def redirect_plex():
    pass


@app.get('/redirect/<type_>/<ident>')
@app.get('/redirect/<type_>/<ident>/<season>/<episode>')
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


@app.get(
    '/stream/<type>/<tmdb_id>',
    response_class=StreamingResponse,
    responses={200: {"model": ITorrent, "content": {'text/event-stream': {}}}},
)
def stream(
    type: MediaType,
    tmdb_id: int,
    season: Optional[int] = None,
    episode: Optional[int] = None,
):
    ...


class DownloadAllResponse(BaseModel):
    packs: List[ITorrent]
    complete: List[Tuple[str, List[ITorrent]]]
    incomplete: List[Tuple[str, List[ITorrent]]]


@app.get(
    '/select/<tmdb_id>/season/<season>/download_all', response_model=DownloadAllResponse
)
def select(tmdb_id: int, season: int):
    pass


@app.get('/diagnostics')
def diagnostics():
    pass


class DownloadPost(Orm):
    magnet: str
    tmdb_id: int
    season: Optional[int] = None
    episode: Optional[int] = None

    _valid_magnet = validator('magnet')(lambda field: re.search(r'^magnet:', field))


@app.post('/download', response_model=DownloadResponse)
def download_post(download: DownloadPost):
    ...


@app.get('/index')
def index():
    pass


class Stats(BaseModel):
    episode: int
    movie: int


class StatsResponse(BaseModel):
    user: str
    values: Stats


@app.get('/stats', response_model=List[StatsResponse])
def stats():
    ...


class MovieResponse(BaseModel):
    title: str
    imdb_id: str


@app.get('/movie/<tmdb_id>', response_model=MovieResponse)
def movie(tmdb_id: int):
    movie = get_movie(tmdb_id)
    return {"title": movie['title'], "imdb_id": movie['imdb_id']}


@app.get('/torrents')
def torrents():
    pass


class SearchResponse(BaseModel):
    title: str
    type: MediaType
    year: int
    imdbID: int


@app.get('/search', response_model=List[SearchResponse])
async def search(query: str):
    ...


class MonitorPost(Orm):
    tmdb_id: int
    type: FMediaType


class UserShim(Orm):
    username: str


class MonitorGet(MonitorPost):
    id: int
    title: str
    added_by: str

    Config = map_to({'added_by': 'added_by.username'})


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


@monitor_ns.delete('/<monitor_id>', tags=['monitor'])
def monitor_delete(monitor_id: int):
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


@monitor_ns.post('', tags=['monitor'], response_model=MonitorGet)
def monitor_post(monitor: MonitorPost, user: User = Depends(get_current_user)):
    title = (
        get_tv(monitor.tmdb_id)['name']
        if monitor.type == FMediaType.TV
        else get_movie(monitor.tmdb_id)['title']
    )

    v = {
        **monitor.dict(),
        'type': monitor.type.name,
        'title': title,
        "added_by": db.session.query(User).first(),
    }
    m = Monitor(**v)

    db.session.add(m)
    db.session.commit()

    return m


tv_ns = APIRouter()


class SeasonMeta(BaseModel):
    episode_count: int
    season_number: int


class TvResponse(BaseModel):
    number_of_seasons: int
    title: str
    imdb_id: str
    seasons: List[SeasonMeta]


@tv_ns.get('/<tmdb_id>', tags=['tv'], response_model=TvResponse)
def api_tv(tmdb_id: int):
    tv = get_tv(tmdb_id)
    return {**tv, 'imdb_id': get_tv_imdb_id(tmdb_id), 'title': tv['name']}


class Episode(BaseModel):
    name: str
    id: int
    episode_number: int
    air_date: Optional[date]


class TvSeasonResponse(BaseModel):
    episodes: List[Episode]


@tv_ns.get('/<tmdb_id>/season/<season>', tags=['tv'], response_model=TvSeasonResponse)
def api_tv_season(tmdb_id: int, season: int):
    return get_tv_episodes(tmdb_id, season)


app.include_router(tv_ns, prefix='/tv')
app.include_router(monitor_ns, prefix='/monitor')


def call_sync(method='GET', path='/monitor', query_string='', headers=None):
    response: Dict[str, Any] = {}

    async def send(message):
        response.update(message)

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
            lambda: [],
            send,
        )

    get_event_loop().run_until_complete(call())

    response.pop('type')
    if 'body' in response:
        response['response'] = response.pop('body')
    response['headers'] = dict(response['headers'])
    response['mimetype'] = response['headers'].pop(b'content-type').decode()

    return Response(**response)


if __name__ == "__main__":
    print(call_sync())
