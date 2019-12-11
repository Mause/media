from typing import List, Optional, Type, TypeVar, Union

from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import joinedload, relationship
from sqlalchemy_repr import RepresentableBase

db = SQLAlchemy(model_class=RepresentableBase)
T = TypeVar('T')


class Download(db.Model):  # type: ignore
    __tablename__ = 'download'
    id = Column(Integer, primary_key=True)
    transmission_id = Column(String, nullable=False)
    imdb_id = Column(String, nullable=False)
    type = Column(String)
    movie = relationship('MovieDetails', uselist=False, cascade='all,delete')
    movie_id = Column(Integer, ForeignKey('movie_details.id', ondelete='CASCADE'))
    episode = relationship('EpisodeDetails', uselist=False, cascade='all,delete')
    episode_id = Column(Integer, ForeignKey('episode_details.id', ondelete='CASCADE'))
    title = Column(String)


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
