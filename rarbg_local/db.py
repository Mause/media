import enum
import logging
import sqlite3
from collections.abc import AsyncGenerator, Callable, Coroutine, Sequence
from datetime import datetime
from typing import Annotated, Any, Never, cast

import backoff
import logfire
import psycopg
import sqlalchemy.pool.base
from fastapi import Depends
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    delete,
    event,
)
from sqlalchemy.dialects.sqlite.aiosqlite import AsyncAdapt_aiosqlite_connection
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.future import select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    joinedload,
    mapped_column,
    relationship,
)
from sqlalchemy.orm.attributes import CALLABLES_OK, instance_dict, instance_state
from sqlalchemy.orm.base import PassiveFlag
from sqlalchemy.orm.state import SQL_OK
from sqlalchemy.sql import ClauseElement, func
from sqlalchemy.types import Enum
from sqlalchemy.util.concurrency import greenlet_spawn
from sqlalchemy_repr import RepresentableBase

from .settings import Settings, get_settings
from .singleton import singleton
from .types import ImdbId, TmdbId
from .utils import format_marker, precondition

logger = logging.getLogger(__name__)


class Awaitable[T: Base]:
    parent: T

    def __init__(self, parent: T) -> None:
        self.parent: T = parent

    def __getattr__(self, name: str) -> Coroutine[Any, Any, Any]:
        passive = CALLABLES_OK + PassiveFlag.NO_RAISE + SQL_OK
        do_get = getattr(type(self.parent), name).impl.get

        return greenlet_spawn(
            do_get, instance_state(self.parent), instance_dict(self.parent), passive
        )


class Base(RepresentableBase, DeclarativeBase):
    type_annotation_map = {
        TmdbId: Integer,
        ImdbId: String,
    }

    @property
    def awaitable_attrs(self) -> Awaitable['Base']:
        return Awaitable(self)


class Download(Base):
    __tablename__ = 'download'
    _json_exclude = {'movie', 'episode'}
    _json_include = {'added_by'}
    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[TmdbId | None]
    transmission_id: Mapped[str]
    imdb_id: Mapped[ImdbId]
    type: Mapped[str]
    movie: Mapped['MovieDetails'] = relationship(
        uselist=False,
        cascade='all,delete',
        lazy='raise',
    )
    movie_id: Mapped[int | None] = mapped_column(
        ForeignKey('movie_details.id', ondelete='CASCADE')
    )
    episode: Mapped['EpisodeDetails'] = relationship(
        uselist=False,
        cascade='all,delete',
        lazy='raise',
    )
    episode_id: Mapped[int | None] = mapped_column(
        ForeignKey('episode_details.id', ondelete='CASCADE')
    )
    title: Mapped[str]
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    added_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    added_by: Mapped['User'] = relationship(
        back_populates='downloads',
        lazy='raise',
    )


class EpisodeDetails(Base):
    __tablename__ = 'episode_details'
    id: Mapped[int] = mapped_column(primary_key=True)
    download: Mapped['Download'] = relationship(
        back_populates='episode', passive_deletes=True, uselist=False, lazy='raise'
    )
    show_title: Mapped[str]
    season: Mapped[int]
    episode: Mapped[int | None]

    def is_season_pack(self) -> bool:
        return self.episode is None

    def __repr__(self) -> str:
        return self.show_title + ' ' + format_marker(self.season, self.episode)


class MovieDetails(Base):
    __tablename__ = 'movie_details'
    id: Mapped[int] = mapped_column(primary_key=True)
    download: Mapped['Download'] = relationship(
        back_populates='movie', passive_deletes=True, uselist=False, lazy='raise'
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
    roles: Mapped[list['Role']] = relationship(
        secondary='user_roles',
        uselist=True,
        lazy='raise',
    )

    downloads: Mapped[list[Download]] = relationship(lazy='raise')

    def __repr__(self) -> str:
        return self.username

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, User) and self.id == other.id


# Define the Role data-model
class Role(Base):
    __tablename__ = 'roles'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    def __repr__(self) -> str:
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
    tmdb_id: Mapped[TmdbId]

    added_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    added_by: Mapped['User'] = relationship(lazy='raise')

    title: Mapped[str]
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


async def get_all[T](session: AsyncSession, model: type[T]) -> Sequence[T]:
    if model == MovieDetails:
        joint = MovieDetails.download
    elif model == EpisodeDetails:
        joint = EpisodeDetails.download
    else:
        raise ValueError(f'Unknown model: {model}')
    return (
        (
            await session.execute(
                select(model).options(joinedload(joint).joinedload(Download.added_by))
            )
        )
        .scalars()
        .all()
    )


async def get_episodes(session: AsyncSession) -> Sequence[EpisodeDetails]:
    return await get_all(session, EpisodeDetails)


async def get_movies(session: AsyncSession) -> Sequence[MovieDetails]:
    return await get_all(session, MovieDetails)


async def get_or_create[T](
    session: AsyncSession, model: type[T], defaults: Any = None, **kwargs: Any
) -> T:
    instance = (
        (await session.execute(select(model).filter_by(**kwargs))).scalars().first()
    )
    if instance:
        return instance
    params = {k: v for k, v in kwargs.items() if not isinstance(v, ClauseElement)}
    params.update(defaults or {})
    instance: T = model(**params)  # type: ignore
    session.add(instance)
    return cast(T, instance)


def normalise_db_url(database_url: str) -> URL:
    parsed = make_url(database_url)
    if parsed.get_backend_name() in ('postgres', 'postgresql'):
        parsed = parsed.set(drivername='postgresql+psycopg')
    return parsed


def normalise_db_url_async(database_url: str) -> URL:
    url = make_url(database_url)
    return url.set(
        drivername=(
            'sqlite+aiosqlite'
            if url.get_backend_name() == 'sqlite'
            else 'postgresql+psycopg'
        )
    )


MAX_TRIES = 5


@singleton
def get_engine(settings: Annotated[Settings, Depends(get_settings)]) -> Engine:
    return build_engine(normalise_db_url(settings.database_url), create_engine)


def listens_for(
    engine: Engine | AsyncEngine, event_name: str
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    if isinstance(engine, AsyncEngine):
        return event.listens_for(engine.sync_engine, event_name)
    else:
        return event.listens_for(engine, event_name)


def build_engine[T: Engine | AsyncEngine](db_url: URL, cr: Callable[..., T]) -> T:
    logger.info('db_url: %s', db_url)

    sqlite = db_url.get_backend_name() == 'sqlite'
    if sqlite:
        engine = cr(
            db_url, connect_args={"check_same_thread": False}, echo_pool='debug'
        )

        @listens_for(engine, 'connect')
        def _fk_pragma_on_connect(
            dbapi_con: sqlite3.Connection,
            con_record: sqlalchemy.pool.base._ConnectionRecord,
        ) -> None:
            if isinstance(dbapi_con, AsyncAdapt_aiosqlite_connection):
                dbapi_con = dbapi_con.driver_connection._connection
            dbapi_con.create_collation(
                "en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1
            )
            dbapi_con.execute('pragma foreign_keys=ON')

    else:
        engine = cr(
            db_url, max_overflow=10, pool_size=5, pool_recycle=300, echo_pool='debug'
        )

        if not engine.dialect.is_async:

            @listens_for(engine, "do_connect")
            @backoff.on_exception(
                backoff.fibo,
                psycopg.OperationalError,
                max_tries=MAX_TRIES,
                giveup=lambda e: "too many connections for role" not in e.args[0],
            )
            def receive_do_connect(
                dialect: Never, conn_rec: Never, cargs: tuple, cparams: dict
            ) -> psycopg.Connection:
                return psycopg.connect(*cargs, **cparams)

    logfire.instrument_sqlalchemy(engine=engine)

    return engine


async def get_async_engine(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncEngine:
    return build_engine(
        normalise_db_url_async(settings.database_url), create_async_engine
    )


@singleton
def get_async_sessionmaker(
    engine: Annotated[AsyncEngine, Depends(get_async_engine)],
) -> async_sessionmaker:
    return async_sessionmaker(autocommit=False, autoflush=True, bind=engine)


async def get_async_db(
    session_local: Annotated[async_sessionmaker, Depends(get_async_sessionmaker)],
) -> AsyncGenerator[AsyncSession, None]:
    sl = session_local()
    try:
        yield sl
    finally:
        await sl.close()


async def safe_delete[T](session: AsyncSession, entity: type[T], id: int) -> None:
    query = await session.execute(delete(entity).filter_by(id=id))
    precondition(query.rowcount > 0, 'Nothing to delete')
    await session.commit()
