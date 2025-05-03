import enum
import logging
from datetime import datetime
from functools import lru_cache
from typing import List, Optional, Type, TypeVar, Union, cast

import backoff
import psycopg2
from fastapi import Depends
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    event,
)
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    RelationshipProperty,
    Session,
    joinedload,
    relationship,
    sessionmaker,
)
from sqlalchemy.sql import ClauseElement, func
from sqlalchemy.types import Enum
from sqlalchemy_repr import RepresentableBase

from .settings import Settings, get_settings
from .singleton import singleton
from .utils import precondition

Base = declarative_base(cls=RepresentableBase)
logger = logging.getLogger(__name__)
T = TypeVar('T')


class Download(Base):  # type: ignore
    __tablename__ = 'download'
    _json_exclude = {'movie', 'episode'}
    _json_include = {'added_by'}
    id = Column(Integer, primary_key=True)
    tmdb_id = Column(Integer, default=None)
    transmission_id = Column(String, nullable=False)
    imdb_id = Column(String, nullable=False)
    type = Column(String)
    movie: RelationshipProperty['MovieDetails'] = relationship(
        'MovieDetails', uselist=False, cascade='all,delete'
    )
    movie_id = Column(Integer, ForeignKey('movie_details.id', ondelete='CASCADE'))
    episode: RepresentableBase['EpisodeDetails'] = relationship(
        'EpisodeDetails', uselist=False, cascade='all,delete'
    )
    episode_id = Column(Integer, ForeignKey('episode_details.id', ondelete='CASCADE'))
    title = Column(String)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    added_by_id = Column(Integer, ForeignKey('users.id'))
    added_by: RelationshipProperty['User'] = relationship(
        'User', back_populates='downloads'
    )

    def progress(self):
        from .main import get_keyed_torrents

        return get_keyed_torrents()[self.transmission_id]['percentDone'] * 100


class EpisodeDetails(Base):  # type: ignore
    __tablename__ = 'episode_details'
    id = Column(Integer, primary_key=True)
    download: RelationshipProperty[Download] = relationship(
        'Download', back_populates='episode', passive_deletes=True, uselist=False
    )
    show_title = Column(String, nullable=False)
    season = Column(Integer, nullable=False)
    episode = Column(Integer)

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


class MovieDetails(Base):  # type: ignore
    __tablename__ = 'movie_details'
    id = Column(Integer, primary_key=True)
    download: RelationshipProperty[Download] = relationship(
        'Download', back_populates='movie', passive_deletes=True, uselist=False
    )


class User(Base):  # type: ignore
    __tablename__ = 'users'
    _json_exclude = {'roles', 'password', 'downloads'}
    id = Column(Integer, primary_key=True)
    active = Column('is_active', Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='en_AU' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = Column(String(255, collation='en_AU'), nullable=False, unique=True)
    password = Column(String(255), nullable=False, server_default='')

    email = Column(String(255, collation='en_AU'), nullable=True, unique=True)

    # User information
    first_name = Column(
        String(100, collation='en_AU'), nullable=False, server_default=''
    )
    last_name = Column(
        String(100, collation='en_AU'), nullable=False, server_default=''
    )

    # Define the relationship to Role via UserRoles
    roles = relationship('Role', secondary='user_roles')

    downloads = relationship('Download')

    def __repr__(self):
        return self.username

    def __eq__(self, other):
        return isinstance(other, User) and self.id == other.id


# Define the Role data-model
class Role(Base):  # type: ignore
    __tablename__ = 'roles'
    id = Column(Integer(), primary_key=True)
    name = Column(String(50), unique=True)

    def __repr__(self):
        return self.name


class _Roles:
    Admin: Role
    Member: Role

    @lru_cache()
    def __getattr__(self, name):
        return get_or_create(Role, name=name)


Roles = _Roles()


# Define the UserRoles association table
class UserRoles(Base):  # type: ignore
    __tablename__ = 'user_roles'
    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), ForeignKey('users.id', ondelete='CASCADE'))
    role_id = Column(Integer(), ForeignKey('roles.id', ondelete='CASCADE'))


class MonitorMediaType(enum.Enum):
    MOVIE = 'MOVIE'
    TV = 'TV'


class Monitor(Base):  # type: ignore
    __tablename__ = 'monitor'

    id = Column(Integer(), primary_key=True)
    tmdb_id = Column(Integer)

    added_by_id = Column(Integer, ForeignKey('users.id'))
    added_by: RelationshipProperty['User'] = relationship('User')

    title = Column(String, nullable=False)
    type = Column(
        Enum(MonitorMediaType),
        default=MonitorMediaType.MOVIE.name,
        nullable=False,
        server_default=MonitorMediaType.MOVIE.name,
    )


def create_download(
    *,
    transmission_id: str,
    imdb_id: str,
    title: str,
    type: str,
    tmdb_id: int,
    details: Union[MovieDetails, EpisodeDetails],
    id: Optional[int] = None,
    added_by: User,
    timestamp: Optional[datetime] = None,
) -> Download:
    precondition(not imdb_id or imdb_id.startswith('tt'), f'Invalid imdb_id: {imdb_id}')
    return Download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        title=title,
        type=type,
        tmdb_id=tmdb_id,
        **{type: details},
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
    timestamp: Optional[datetime] = None,
) -> MovieDetails:
    md = MovieDetails()
    md.download = create_download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        title=title,
        type='movie',
        tmdb_id=tmdb_id,
        details=md,
        added_by=added_by,
        timestamp=timestamp,
    )
    return md


def create_episode(
    *,
    transmission_id: str,
    imdb_id: str,
    season: int,
    episode: Optional[int],
    title: str,
    tmdb_id: int,
    id: Optional[int] = None,
    show_title: str,
    added_by: User,
    download_id: Optional[int] = None,
    timestamp: Optional[datetime] = None,
) -> EpisodeDetails:
    ed = EpisodeDetails(id=id, season=season, episode=episode, show_title=show_title)
    ed.download = create_download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        tmdb_id=tmdb_id,
        title=title,
        type='episode',
        details=ed,
        id=download_id,
        timestamp=timestamp,
        added_by=added_by,
    )
    return ed


def get_all(session: Session, model: Type[T]) -> List[T]:
    return session.query(model).options(joinedload('download')).all()


def get_episodes(session: Session) -> List[EpisodeDetails]:
    return get_all(session, EpisodeDetails)


def get_movies(session: Session) -> List[MovieDetails]:
    return get_all(session, MovieDetails)


def get_or_create(session: Session, model: Type[T], defaults=None, **kwargs) -> T:
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = {k: v for k, v in kwargs.items() if not isinstance(v, ClauseElement)}
    params.update(defaults or {})
    instance: T = model(**params)  # type: ignore
    session.add(instance)
    return cast(T, instance)


def normalise_db_url(database_url: str) -> URL:
    parsed = make_url(database_url)
    if parsed.drivername == 'postgres':
        parsed = parsed.set(drivername='postgresql')
    return parsed


@singleton
def get_session_local(settings: Settings = Depends(get_settings)):
    db_url = normalise_db_url(settings.database_url)

    logger.info('db_url: %s', db_url)

    sqlite = db_url.drivername == 'sqlite'
    if sqlite:
        engine = create_engine(
            db_url, connect_args={"check_same_thread": False}, echo_pool='debug'
        )

        @event.listens_for(engine, 'connect')
        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.create_collation(
                "en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1
            )
            dbapi_con.execute('pragma foreign_keys=ON')

    else:
        engine = create_engine(
            db_url, max_overflow=10, pool_size=5, pool_recycle=300, echo_pool='debug'
        )

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


def get_db(session_local=Depends(get_session_local)):
    sl = session_local()
    try:
        yield sl
    finally:
        sl.close()
