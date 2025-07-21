from contextvars import ContextVar
from datetime import datetime, timezone

from factory import Factory, Faker, List, Maybe, SubFactory, lazy_attribute
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDateTime

from ..db import Download, EpisodeDetails, MovieDetails, User
from ..models import (
    DownloadAllResponse,
    DownloadPost,
    Episode,
    EpisodeInfo,
    ITorrent,
    MovieResponse,
    ProviderSource,
    SeasonMeta,
    TvApiResponse,
    TvResponse,
    TvSeasonResponse,
)

session_var = ContextVar('session', default=None)
imdb_id = Faker('numerify', text='tt######')


class SQLFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session_factory = session_var.get


class EpisodeFactory(Factory):
    class Meta:
        model = Episode

    name = Faker('name')
    id = Faker('random_number')
    episode_number = Faker('random_number')
    air_date = Faker('date')


class TvSeasonResponseFactory(Factory):
    class Meta:
        model = TvSeasonResponse

    episodes = List([SubFactory(EpisodeFactory)])


class SeasonFactory(Factory):
    class Meta:
        model = SeasonMeta

    episode_count = Faker('random_number')
    season_number = Faker('random_number')


class TvBaseResponseFactory(Factory):
    number_of_seasons = lazy_attribute(lambda a: len(a.seasons))
    seasons = List([SubFactory(SeasonFactory)])


class TvResponseFactory(TvBaseResponseFactory):
    class Meta:
        model = TvResponse

    title = Faker('name')
    imdb_id = imdb_id


class TvApiResponseFactory(TvBaseResponseFactory):
    class Meta:
        model = TvApiResponse

    name = Faker('name')


class MovieResponseFactory(Factory):
    class Meta:
        model = MovieResponse

    imdb_id = imdb_id
    title = Faker('name')


class EpisodeInfoFactory(Factory):
    class Meta:
        model = EpisodeInfo

    seasonnum = Faker('random_number')
    epnum = Faker('random_number')


class ITorrentFactory(Factory):
    class Meta:
        model = ITorrent

    source = FuzzyChoice(ProviderSource)
    title = Faker('file_name')
    seeders = Faker('random_number')
    download = lazy_attribute(lambda a: 'magnet://' + a.title)
    category = FuzzyChoice(['A', 'B', 'C'])
    episode_info = SubFactory(EpisodeInfoFactory)


ITorrentList = List([ITorrentFactory.build()])
PackList = List([List([Faker('file_name'), ITorrentList])])


class DownloadAllResponseFactory(Factory):
    class Meta:
        model = DownloadAllResponse

    packs = ITorrentList
    complete = PackList
    incomplete = PackList


class UserFactory(SQLFactory):
    class Meta:
        model = User

    username = Faker('name')


class DownloadFactory(SQLFactory):
    class Meta:
        model = Download

    added_by = SubFactory(UserFactory)
    title = Faker('name')

    tmdb_id = Faker('random_number')
    transmission_id = Faker('uuid4')
    imdb_id = imdb_id
    timestamp = FuzzyDateTime(start_dt=datetime(2000, 1, 1, tzinfo=timezone.utc))


class EpisodeDetailsFactory(SQLFactory):
    class Meta:
        model = EpisodeDetails

    show_title = Faker('name')
    download = SubFactory(DownloadFactory, type='EPISODE')

    season = Faker('random_number')
    episode = Faker('random_number')


class MovieDetailsFactory(SQLFactory):
    class Meta:
        model = MovieDetails

    download = SubFactory(DownloadFactory, type='MOVIE')


class DownloadPostFactory(Factory):
    class Meta:
        model = DownloadPost

    class Params:
        is_tv = Faker('boolean')
        filename = Faker('file_name')

    tmdb_id = Faker('random_number')
    magnet = lazy_attribute(lambda a: 'magnet://' + a.filename)
    season = Maybe('is_tv', yes_declaration=Faker('random_number'))
    episode = Maybe('is_tv', yes_declaration=Faker('random_number'))
