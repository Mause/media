from functools import lru_cache
from typing import List, Optional, Type, TypeVar, Union

from flask_jsontools import JsonSerializableBase
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import joinedload, relationship
from sqlalchemy.sql import ClauseElement
from sqlalchemy_repr import RepresentableBase

db = SQLAlchemy(model_class=(RepresentableBase, JsonSerializableBase))
T = TypeVar('T')


class Download(db.Model):  # type: ignore
    __tablename__ = 'download'
    _json_exclude = {'movie', 'episode'}
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


class MovieDetails(db.Model):  # type: ignore
    __tablename__ = 'movie_details'
    id = Column(Integer, primary_key=True)
    download = relationship(
        'Download', back_populates='movie', passive_deletes=True, uselist=False
    )


class User(db.Model, UserMixin):  # type: ignore
    __tablename__ = 'users'
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


# Define the Role data-model
class Role(db.Model):  # type: ignore
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return self.name


class _Roles:
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


def create_download(
    transmission_id: str,
    imdb_id: str,
    title: str,
    type: str,
    details: Union[MovieDetails, EpisodeDetails],
    id: int = None,
):
    assert imdb_id.startswith('tt'), imdb_id
    return Download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        title=title,
        type=type,
        **{type: details},
        id=id,
    )


def create_movie(transmission_id: str, imdb_id: str, title: str) -> None:
    md = MovieDetails()
    db.session.add(md)
    db.session.add(create_download(transmission_id, imdb_id, title, 'movie', md))


def create_episode(
    transmission_id: str,
    imdb_id: str,
    season: str,
    episode: Optional[str],
    title: str,
    id: int = None,
    download_id: int = None,
    show_title: str = None,
) -> EpisodeDetails:
    ed = EpisodeDetails(id=id, season=season, episode=episode, show_title=show_title)
    db.session.add(ed)
    db.session.add(
        create_download(transmission_id, imdb_id, title, 'episode', ed, id=download_id)
    )
    return ed


def get_all(model: Type[T]) -> List[T]:
    return db.session.query(model).options(joinedload('download')).all()


def get_episodes() -> List[EpisodeDetails]:
    return get_all(EpisodeDetails)


def get_movies() -> List[MovieDetails]:
    return get_all(MovieDetails)


def get_or_create(model: Type[T], defaults=None, **kwargs) -> T:
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = {k: v for k, v in kwargs.items() if not isinstance(v, ClauseElement)}
    params.update(defaults or {})
    instance: T = model(**params)  # type: ignore
    db.session.add(instance)
    return instance
