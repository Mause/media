import enum
from datetime import datetime
from functools import lru_cache
from typing import List, Optional, Type, TypeVar, Union

from flask_jsontools import JsonSerializableBase
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin, current_user
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session, joinedload, relationship
from sqlalchemy.sql import ClauseElement, func
from sqlalchemy.types import Enum
from sqlalchemy_repr import RepresentableBase

from .utils import precondition

db = SQLAlchemy(model_class=(RepresentableBase, JsonSerializableBase))
T = TypeVar('T')


class Download(db.Model):  # type: ignore
    __tablename__ = 'download'
    _json_exclude = {'movie', 'episode'}
    _json_include = {'added_by'}
    id = Column(Integer, primary_key=True)
    tmdb_id = Column(Integer, default=None)
    transmission_id = Column(String, nullable=False)
    imdb_id = Column(String, nullable=False)
    type = Column(String)
    movie = relationship('MovieDetails', uselist=False, cascade='all,delete')
    movie_id = Column(Integer, ForeignKey('movie_details.id', ondelete='CASCADE'))
    episode = relationship('EpisodeDetails', uselist=False, cascade='all,delete')
    episode_id = Column(Integer, ForeignKey('episode_details.id', ondelete='CASCADE'))
    title = Column(String)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    added_by_id = Column(Integer, ForeignKey('users.id'))
    added_by = relationship('User', back_populates='downloads')

    def progress(self):
        from .main import get_keyed_torrents

        return get_keyed_torrents()[self.transmission_id]['percentDone'] * 100


class EpisodeDetails(db.Model):  # type: ignore
    __tablename__ = 'episode_details'
    id = Column(Integer, primary_key=True)
    download = relationship(
        'Download', back_populates='episode', passive_deletes=True, uselist=False
    )
    show_title = Column(String, nullable=False)
    season = Column(Integer, nullable=False)
    episode = Column(Integer)

    def is_season_pack(self):
        return self.episode is None

    def get_marker(self):
        return f'S{self.season:02d}E{self.episode:02d}'

    def __repr__(self):
        return (
            self.show_title
            + ' '
            + (self.get_marker() if self.episode else f'S{self.season:02d}')
        )


class MovieDetails(db.Model):  # type: ignore
    __tablename__ = 'movie_details'
    id = Column(Integer, primary_key=True)
    download = relationship(
        'Download', back_populates='movie', passive_deletes=True, uselist=False
    )


class User(db.Model, UserMixin):  # type: ignore
    __tablename__ = 'users'
    _json_exclude = {'roles', 'password', 'downloads'}
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='en_AU' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(db.String(255, collation='en_AU'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    first_name = db.Column(
        db.String(100, collation='en_AU'), nullable=False, server_default=''
    )
    last_name = db.Column(
        db.String(100, collation='en_AU'), nullable=False, server_default=''
    )

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')

    downloads = db.relationship('Download')

    def __repr__(self):
        return self.username

    def __eq__(self, other):
        return isinstance(other, User) and self.id == other.id


# Define the Role data-model
class Role(db.Model):  # type: ignore
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

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
class UserRoles(db.Model):  # type: ignore
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


class MonitorMediaType(enum.Enum):
    MOVIE = 'MOVIE'
    TV = 'TV'


class Monitor(db.Model):  # type: ignore
    id = db.Column(db.Integer(), primary_key=True)
    tmdb_id = Column(Integer)

    added_by_id = Column(Integer, ForeignKey('users.id'))
    added_by = relationship('User')

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
    id: int = None,
    timestamp: datetime = None,
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
        added_by=current_user._get_current_object(),
        timestamp=timestamp,
    )


def create_movie(
    *,
    transmission_id: str,
    imdb_id: str,
    title: str,
    tmdb_id: int,
    timestamp: datetime = None,
) -> MovieDetails:
    md = MovieDetails()
    create_download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        title=title,
        type='movie',
        tmdb_id=tmdb_id,
        details=md,
        timestamp=timestamp,
    )
    return md


def create_episode(
    *,
    transmission_id: str,
    imdb_id: str,
    season: str,
    episode: Optional[str],
    title: str,
    tmdb_id: int,
    id: int = None,
    show_title: str,
    download_id: int = None,
    timestamp: datetime = None,
) -> EpisodeDetails:
    ed = EpisodeDetails(id=id, season=season, episode=episode, show_title=show_title)
    create_download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        tmdb_id=tmdb_id,
        title=title,
        type='episode',
        details=ed,
        id=download_id,
        timestamp=timestamp,
    )
    return ed


def get_all(session: Session, model: Type[T]) -> List[T]:
    return session.query(model).options(joinedload('download')).all()


def get_episodes(session: Session) -> List[EpisodeDetails]:
    return get_all(session, EpisodeDetails)


def get_movies(session: Session) -> List[MovieDetails]:
    return get_all(session, MovieDetails)


def get_or_create(model: Type[T], defaults=None, **kwargs) -> T:
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = {k: v for k, v in kwargs.items() if not isinstance(v, ClauseElement)}
    params.update(defaults or {})
    instance: T = model(**params)  # type: ignore
    db.session.add(instance)
    return instance
