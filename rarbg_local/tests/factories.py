from datetime import datetime, timezone

import factory
from factory.fuzzy import FuzzyChoice, FuzzyDateTime

from ..db import Download, EpisodeDetails, MovieDetails, User
from ..models import (
    DownloadAllResponse,
    Episode,
    EpisodeInfo,
    ITorrent,
    MovieResponse,
    ProviderSource,
    SeasonMeta,
    TvResponse,
    TvSeasonResponse,
)

imdb_id = factory.Faker('numerify', text='tt######')


class EpisodeFactory(factory.Factory):
    class Meta:
        model = Episode

    name = factory.Faker('name')
    id = factory.Faker('numerify')
    episode_number = factory.Faker('numerify')
    air_date = factory.Faker('date')


class TvSeasonResponseFactory(factory.Factory):
    class Meta:
        model = TvSeasonResponse

    episodes = factory.List([factory.SubFactory(EpisodeFactory)])


class SeasonFactory(factory.Factory):
    class Meta:
        model = SeasonMeta

    episode_count = factory.Faker('numerify')
    season_number = factory.Faker('numerify')


class TvResponseFactory(factory.Factory):
    class Meta:
        model = TvResponse

    title = factory.Faker('name')
    number_of_seasons = factory.LazyAttribute(lambda a: len(a.seasons))
    seasons = factory.List([factory.SubFactory(SeasonFactory)])


class MovieResponseFactory(factory.Factory):
    class Meta:
        model = MovieResponse

    imdb_id = imdb_id
    title = factory.Faker('name')


class EpisodeInfoFactory(factory.Factory):
    class Meta:
        model = EpisodeInfo

    seasonnum = factory.Faker('numerify', text='#')
    epnum = factory.Faker('numerify', text='#')


class ITorrentFactory(factory.Factory):
    class Meta:
        model = ITorrent

    source = FuzzyChoice(ProviderSource)
    title = factory.Faker('file_name')
    seeders = factory.Faker('numerify', text='##')
    download = factory.lazy_attribute(lambda a: 'magnet://' + a.title)
    category = FuzzyChoice(['A', 'B', 'C'])
    episode_info = factory.SubFactory(EpisodeInfoFactory)


ITorrentList = factory.List([ITorrentFactory()])
PackList = factory.List([factory.List([factory.Faker('file_name'), ITorrentList])])


class DownloadAllResponseFactory(factory.Factory):
    class Meta:
        model = DownloadAllResponse

    packs = ITorrentList
    complete = PackList
    incomplete = PackList


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Faker('name')


class DownloadFactory(factory.Factory):
    class Meta:
        model = Download

    added_by = factory.SubFactory(UserFactory)
    title = factory.Faker('name')

    tmdb_id = factory.Faker('numerify', text='######')
    transmission_id = factory.Faker('uuid4')
    imdb_id = imdb_id
    timestamp = FuzzyDateTime(start_dt=datetime(2000, 1, 1, tzinfo=timezone.utc))


class EpisodeDetailsFactory(factory.Factory):
    class Meta:
        model = EpisodeDetails

    show_title = factory.Faker('name')
    download = factory.SubFactory(DownloadFactory, type='EPISODE')

    season = factory.Faker('numerify', text='#')
    episode = factory.Faker('numerify', text='#')


class MovieDetailsFactory(factory.Factory):
    class Meta:
        model = MovieDetails

    download = factory.SubFactory(DownloadFactory, type='MOVIE')
