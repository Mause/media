from typing import List, Union, TypeVar, Type, Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_repr import RepresentableBase
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy import Column, Integer, String, ForeignKey

db = SQLAlchemy(model_class=RepresentableBase)
T = TypeVar('T')


class Download(db.Model):
    __tablename__ = 'download'
    id = Column(Integer, primary_key=True)
    transmission_id = Column(Integer)
    imdb_id = Column(String)
    type = Column(String)
    movie = relationship('MovieDetails', uselist=False, cascade='all,delete')
    movie_id = Column(
        Integer, ForeignKey('movie_details.id', ondelete='CASCADE')
    )
    episode = relationship(
        'EpisodeDetails', uselist=False, cascade='all,delete'
    )
    episode_id = Column(
        Integer, ForeignKey('episode_details.id', ondelete='CASCADE')
    )
    title = Column(String)


class EpisodeDetails(db.Model):
    __tablename__ = 'episode_details'
    id = Column(Integer, primary_key=True)
    download = relationship(
        'Download',
        back_populates='episode',
        passive_deletes=True,
        uselist=False,
    )
    season = Column(Integer)
    episode = Column(Integer)


class MovieDetails(db.Model):
    __tablename__ = 'movie_details'
    id = Column(Integer, primary_key=True)
    download = relationship(
        'Download', back_populates='movie', passive_deletes=True, uselist=False
    )


def create_download(
    transmission_id: int,
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
        id=id
    )


def create_movie(transmission_id: int, imdb_id: str, title: str) -> None:
    md = MovieDetails()
    db.session.add(md)
    db.session.add(
        create_download(transmission_id, imdb_id, title, 'movie', md)
    )


def create_episode(
    transmission_id: int,
    imdb_id: str,
    season: str,
    episode: Optional[str],
    title: str,
    id: int = None,
    download_id: int = None,
) -> EpisodeDetails:
    ed = EpisodeDetails(id=id, season=season, episode=episode)
    db.session.add(ed)
    db.session.add(
        create_download(
            transmission_id, imdb_id, title, 'episode', ed, id=download_id
        )
    )
    return ed


def get_all(model: Type[T]) -> List[T]:
    return db.session.query(model).options(joinedload('download')).all()


def get_episodes() -> List[EpisodeDetails]:
    return get_all(EpisodeDetails)


def get_movies() -> List[MovieDetails]:
    return get_all(MovieDetails)
