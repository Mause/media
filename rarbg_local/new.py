import re
from datetime import date
from enum import Enum
from typing import List, Optional

from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from flask_user import UserManager
from pydantic import BaseModel, validator

from .db import Monitor, User, db
from .tmdb import get_movie, get_tv, get_tv_episodes, get_tv_imdb_id

app = FastAPI()


class FakeApp:
    import_name = __name__

    def __init__(self, fastapi_app):
        self.debug = True
        self.config = {
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_ECHO': True,
        }
        self.extensions = {}

    def teardown_appcontext(self, func):
        pass


fake_app = FakeApp(app)
db.init_app(fake_app)
db.app = fake_app

engine = db.get_engine(fake_app, None)
con = engine.raw_connection().connection
con.create_collation("en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1)

db.create_all()

user_manager = UserManager(None, db, User)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class MediaType(Enum):
    SERIES = 'series'
    MOVIE = 'movie'


class Orm(BaseModel):
    class Config:
        orm_mode = True


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


@app.get('/select/<tmdb_id>/season/<season>/download_all')
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


class ITorrent(BaseModel):
    download: str


@app.post('/download', response_model=DownloadResponse)
def download_post(download: DownloadPost):
    ...


@app.get('/index')
def index():
    pass


@app.get('/stats')
def stats():
    pass


@app.get('/movie/<tmdb_id>')
def movie(tmdb_id: int):
    pass


@app.get('/torrents')
def torrents():
    pass


@app.get('/search')
def search(query: str):
    pass


class FMediaType(Enum):
    MOVIE = 'movie'
    TV = 'tv'


class MonitorPost(Orm):
    tmdb_id: int
    type: FMediaType


class UserShim(Orm):
    username: str


class MonitorGet(MonitorPost):
    id: int
    title: str
    added_by: UserShim


monitor_ns = APIRouter()


@monitor_ns.get('', tags=['monitor'], response_model=List[MonitorGet])
def monitor_get(token: str = Depends(oauth2_scheme)):
    return db.session.query(Monitor).all()


@monitor_ns.delete('/<monitor_id>', tags=['monitor'])
def monitor_delete(monitor_id: int):
    ...


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.session.query(User).filter_by(username=form_data.username).one_or_none()

    if user_manager.verify_password(
        form_data.password, user.password if user else None
    ):
        return {"access_token": user.username, "token_type": "bearer"}

    raise HTTPException(status_code=400, detail="Incorrect username or password")


@monitor_ns.post('', tags=['monitor'], response_model=MonitorGet)
def monitor_post(monitor: MonitorPost, token: str = Depends(oauth2_scheme)):
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
