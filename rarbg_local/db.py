import enum
import logging
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Annotated, TypeVar, cast

import backoff
import psycopg2
from fastapi import Depends
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    create_engine,
    delete,
    event,
)
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.future import select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    joinedload,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.sql import ClauseElement, func
from sqlalchemy.types import Enum
from sqlalchemy_repr import RepresentableBase

from .settings import Settings, get_settings
from .singleton import singleton
from .types import ImdbId, TmdbId
from .utils import precondition

logger = logging.getLogger(__name__)
T = TypeVar('T')


class Base(RepresentableBase, DeclarativeBase):
    pass


class Download(Base):
    __tablename__ = 'download'
    _json_exclude = {'movie', 'episode'}
    _json_include = {'added_by'}
    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[TmdbId | None]
    transmission_id: Mapped[str]
    imdb_id: Mapped[ImdbId]
    type: Mapped[str]
    movie: Mapped['MovieDetails'] = relationship(uselist=False, cascade='all,delete')
    movie_id: Mapped[int | None] = mapped_column(
        ForeignKey('movie_details.id', ondelete='CASCADE')
    )
    episode: Mapped['EpisodeDetails'] = relationship(
        uselist=False, cascade='all,delete'
    )
    episode_id: Mapped[int | None] = mapped_column(
        ForeignKey('episode_details.id', ondelete='CASCADE')
    )
    title: Mapped[str]
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    added_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    added_by: Mapped['User'] = relationship(back_populates='downloads')

    def progress(self):
        from .main import get_keyed_torrents

        return get_keyed_torrents()[self.transmission_id]['percentDone'] * 100


class EpisodeDetails(Base):
    __tablename__ = 'episode_details'
    id: Mapped[int] = mapped_column(primary_key=True)
    download: Mapped['Download'] = relationship(
        back_populates='episode', passive_deletes=True, uselist=False
    )
    show_title: Mapped[str] = mapped_column()
    season: Mapped[int] = mapped_column()
    episode: Mapped[int | None] = mapped_column()

    def is_season_pack(self):
        return self.episode is None

    def get_marker(self):
        return f'S{int(self.season):02d}E{int(self.episode):02d}'

    def __repr__(self):
        return (
            self.show_title
            + ' '
            + (self.get_marker() if self.episode else f'S{int(self.season):02d}')
        )


class MovieDetails(Base):
    __tablename__ = 'movie_details'
    id: Mapped[int] = mapped_column(primary_key=True)
    download: Mapped['Download'] = relationship(
        back_populates='movie', passive_deletes=True, uselist=False
    )


class User(Base):
    __tablename__ = 'users'
    _json_exclude = {'roles', 'password', 'downloads'}
    id: Mapped[int] = mapped_column(primary_key=True)
    active: Mapped[bool] = mapped_column('is_active', server_default='1')

    # User authentication information. The collation='en_AU' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username: Mapped[str] = mapped_column(String(255, collation='en_AU'), unique=True)
    password: Mapped[str] = mapped_column(String(255), server_default='')

    email: Mapped[str | None] = mapped_column(
        String(255, collation='en_AU'), unique=True
    )

    # User information
    first_name: Mapped[str] = mapped_column(
        String(100, collation='en_AU'), server_default=''
    )
    last_name: Mapped[str] = mapped_column(
        String(100, collation='en_AU'), server_default=''
    )

    # Define the relationship to Role via UserRoles
    roles: Mapped[list['Role']] = relationship(secondary='user_roles', uselist=True)

    downloads: Mapped[list[Download]] = relationship()

    def __repr__(self):
        return self.username

    def __eq__(self, other):
        return isinstance(other, User) and self.id == other.id


# Define the Role data-model
class Role(Base):
    __tablename__ = 'roles'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    def __repr__(self):
        return self.name


# Define the UserRoles association table
class UserRoles(Base):
    __tablename__ = 'user_roles'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id', ondelete='CASCADE'))


class MonitorMediaType(enum.Enum):
    MOVIE = 'MOVIE'
    TV = 'TV'


class Monitor(Base):
    __tablename__ = 'monitor'

    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[TmdbId] = mapped_column()

    added_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    added_by: Mapped['User'] = relationship('User')

    title: Mapped[str] = mapped_column(String())
    type: Mapped[MonitorMediaType] = mapped_column(
        Enum(MonitorMediaType),
        default=MonitorMediaType.MOVIE.name,
        server_default=MonitorMediaType.MOVIE.name,
    )

    status: Mapped[bool] = mapped_column(
        default=False,
    )


def create_download(
    *,
    transmission_id: str,
    imdb_id: str,
    title: str,
    type: str,
    tmdb_id: int,
    id: int | None = None,
    added_by: User,
    timestamp: datetime | None = None,
) -> Download:
    precondition(not imdb_id or imdb_id.startswith('tt'), f'Invalid imdb_id: {imdb_id}')
    return Download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        title=title,
        type=type,
        tmdb_id=tmdb_id,
        id=id,
        added_by=added_by,
        timestamp=timestamp,
    )


def create_movie(
    *,
    transmission_id: str,
    imdb_id: str,
    title: str,
    tmdb_id: int,
    added_by: User,
    timestamp: datetime | None = None,
) -> MovieDetails:
    md = MovieDetails()
    md.download = create_download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        title=title,
        type='movie',
        tmdb_id=tmdb_id,
        added_by=added_by,
        timestamp=timestamp,
    )
    return md


def create_episode(
    *,
    transmission_id: str,
    imdb_id: str,
    season: int,
    episode: int | None,
    title: str,
    tmdb_id: int,
    id: int | None = None,
    show_title: str,
    added_by: User,
    download_id: int | None = None,
    timestamp: datetime | None = None,
) -> EpisodeDetails:
    ed = EpisodeDetails(id=id, season=season, episode=episode, show_title=show_title)
    ed.download = create_download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        tmdb_id=tmdb_id,
        title=title,
        type='episode',
        id=download_id,
        timestamp=timestamp,
        added_by=added_by,
    )
    return ed


def get_all(session: Session, model: type[T]) -> Sequence[T]:
    if model == MovieDetails:
        joint = MovieDetails.download
    elif model == EpisodeDetails:
        joint = EpisodeDetails.download
    else:
        raise ValueError(f'Unknown model: {model}')
    return session.execute(select(model).options(joinedload(joint))).scalars().all()


def get_episodes(session: Session) -> Sequence[EpisodeDetails]:
    return get_all(session, EpisodeDetails)


def get_movies(session: Session) -> Sequence[MovieDetails]:
    return get_all(session, MovieDetails)


def get_or_create(session: Session, model: type[T], defaults=None, **kwargs) -> T:
    instance = session.execute(select(model).filter_by(**kwargs)).scalars().first()
    if instance:
        return instance
    params = {k: v for k, v in kwargs.items() if not isinstance(v, ClauseElement)}
    params.update(defaults or {})
    instance: T = model(**params)  # type: ignore
    session.add(instance)
    return cast(T, instance)


def normalise_db_url(database_url: str) -> URL:
    parsed = make_url(database_url)
    if parsed.get_backend_name() == 'postgres':
        parsed = parsed.set(drivername='postgresql')
    return parsed


def normalise_db_url_async(database_url: str) -> URL:
    url = make_url(database_url)
    return url.set(
        drivername=(
            'sqlite+aiosqlite'
            if url.get_backend_name() == 'sqlite'
            else 'postgresql+asyncpg'
        )
    )


MAX_TRIES = 5


@singleton
def get_engine(settings: Annotated[Settings, Depends(get_settings)]) -> Engine:
    return build_engine(normalise_db_url(settings.database_url), create_engine)


def listens_for(engine: Engine | AsyncEngine, event_name: str):
    if isinstance(engine, AsyncEngine):
        return event.listens_for(engine.sync_engine, event_name)
    else:
        return event.listens_for(engine, event_name)


def build_engine(db_url: URL, cr: Callable):
    logger.info('db_url: %s', db_url)

    sqlite = db_url.get_backend_name() == 'sqlite'
    if sqlite:
        engine = cr(
            db_url, connect_args={"check_same_thread": False}, echo_pool='debug'
        )

        @listens_for(engine, 'connect')
        def _fk_pragma_on_connect(dbapi_con, con_record):
            if not hasattr(dbapi_con, 'create_collation'):  # async
                dbapi_con = dbapi_con.driver_connection._connection
            dbapi_con.create_collation(
                "en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1
            )
            dbapi_con.execute('pragma foreign_keys=ON')

    else:
        engine = cr(
            db_url, max_overflow=10, pool_size=5, pool_recycle=300, echo_pool='debug'
        )

        if db_url.get_driver_name() == 'psycopg2':

            @listens_for(engine, "do_connect")
            @backoff.on_exception(
                backoff.fibo,
                psycopg2.OperationalError,
                max_tries=MAX_TRIES,
                giveup=lambda e: "too many connections for role" not in e.args[0],
            )
            def receive_do_connect(dialect, conn_rec, cargs, cparams):
                return psycopg2.connect(*cargs, **cparams)

    return engine


async def get_async_engine(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncEngine:
    return build_engine(
        normalise_db_url_async(settings.database_url), create_async_engine
    )


@singleton
def get_session_local(engine: Annotated[Engine, Depends(get_engine)]) -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=True, bind=engine)


def get_db(session_local=Depends(get_session_local)):
    sl = session_local()
    try:
        yield sl
    finally:
        sl.close()


def safe_delete(session: Session, entity: type[T], id: int):
    query = session.execute(delete(entity).filter_by(id=id))
    precondition(query.rowcount > 0, 'Nothing to delete')
    session.commit()
