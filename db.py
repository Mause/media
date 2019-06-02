import uuid
import sqlite3
from typing import List, Union

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_repr import RepresentableBase
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey

db = SQLAlchemy(model_class=RepresentableBase)


class Download(db.Model):
    __tablename__ = 'download'
    id = Column(Integer, primary_key=True)
    transmission_id = Column(Integer)
    imdb_id = Column(String)
    type = Column(String)
    movie = relationship('MovieDetails', uselist=False, cascade='delete')
    episode = relationship('EpisodeDetails', uselist=False, cascade='delete')
    title = Column(String)


class EpisodeDetails(db.Model):
    __tablename__ = 'episode_details'
    id = Column(Integer, primary_key=True)
    download = relationship('Download', back_populates='episode', uselist=False)
    download_id = Column(Integer, ForeignKey('download.id'))
    season = Column(Integer)
    episode = Column(Integer)


class MovieDetails(db.Model):
    __tablename__ = 'movie_details'
    id = Column(Integer, primary_key=True)
    download = relationship('Download', back_populates='movie', uselist=False)
    download_id = Column(Integer, ForeignKey('download.id'))


def create_download(
    transmission_id: int,
    imdb_id: str,
    title: str,
    type: str,
    details: Union[MovieDetails, EpisodeDetails],
):
    assert imdb_id.startswith('tt'), imdb_id
    return Download(
        transmission_id=transmission_id,
        imdb_id=imdb_id,
        title=title,
        type=type,
        **{type: details}
    )


def create_movie(transmission_id: int, imdb_id: str, title: str) -> None:
    md = MovieDetails()
    db.session.add(md)
    db.session.add(
        create_download(transmission_id, imdb_id, title, 'movie', md)
    )


def create_episode(
    transmission_id: int, imdb_id: str, season: int, episode: int, title: str
) -> None:
    ed = EpisodeDetails(season=season, episode=episode)
    db.session.add(ed)
    db.session.add(
        create_download(transmission_id, imdb_id, title, 'episode', ed)
    )


def get_episodes() -> List[EpisodeDetails]:
    return db.session.query(EpisodeDetails).all()


def get_movies() -> List[MovieDetails]:
    return db.session.query(MovieDetails).all()


def main():
    hash = uuid.uuid4().hex
    session = Session()
    create_movie(
        session, hash=hash, imdb_id='tt0000000', title='Woman Incoming'
    )
    create_episode(
        session, uuid.uuid4().hex, 'tt0000000', 2, 1, 'American Gods'
    )

    print([d.asdict() for d in session.query(Download).all()])


if __name__ == '__main__':
    main()
