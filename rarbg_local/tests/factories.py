from datetime import datetime, timezone

from factory import Factory, Faker, List, SubFactory, lazy_attribute
from factory.fuzzy import FuzzyChoice, FuzzyDateTime

from ..db import Download, EpisodeDetails, Monitor, MovieDetails, User
from ..models import (
    DownloadAllResponse,
    Episode,
    EpisodeInfo,
    ITorrent,
    MonitorMediaType,
    MovieResponse,
    ProviderSource,
    SeasonMeta,
    TvApiResponse,
    TvResponse,
    TvSeasonResponse,
)

imdb_id = Faker('numerify', text='tt######')


class EpisodeFactory(Factory):
    class Meta:
        model = Episode

    name = Faker('name')
    id = Faker('numerify')
    episode_number = Faker('numerify')
    air_date = Faker('date')


class TvSeasonResponseFactory(Factory):
    class Meta:
        model = TvSeasonResponse

    episodes = List([SubFactory(EpisodeFactory)])


class SeasonFactory(Factory):
    class Meta:
        model = SeasonMeta

    episode_count = Faker('numerify')
    season_number = Faker('numerify')


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

    id = Faker('numerify')
    name = Faker('name')


class MovieResponseFactory(Factory):
    class Meta:
        model = MovieResponse

    imdb_id = imdb_id
    title = Faker('name')


class EpisodeInfoFactory(Factory):
    class Meta:
        model = EpisodeInfo

    seasonnum = Faker('numerify', text='#')
    epnum = Faker('numerify', text='#')


class ITorrentFactory(Factory):
    class Meta:
        model = ITorrent

    source = FuzzyChoice(ProviderSource)
    title = Faker('file_name')
    seeders = Faker('numerify', text='##')
    download = lazy_attribute(lambda a: 'magnet://' + a.title)
    category = FuzzyChoice(['A', 'B', 'C'])
    episode_info = SubFactory(EpisodeInfoFactory)


ITorrentList = List([ITorrentFactory()])
PackList = List([List([Faker('file_name'), ITorrentList])])


class DownloadAllResponseFactory(Factory):
    class Meta:
        model = DownloadAllResponse

    packs = ITorrentList
    complete = PackList
    incomplete = PackList


class UserFactory(Factory):
    class Meta:
        model = User

    username = Faker('name')


class MonitorFactory(Factory):
    class Meta:
        model = Monitor

    id = Faker('numerify')
    type = FuzzyChoice(MonitorMediaType)

    tmdb_id = Faker('numerify')

    added_by = SubFactory(UserFactory)

    title = Faker('name')


class DownloadFactory(Factory):
    class Meta:
        model = Download

    added_by = SubFactory(UserFactory)
    title = Faker('name')

    tmdb_id = Faker('numerify', text='######')
    transmission_id = Faker('uuid4')
    imdb_id = imdb_id
    timestamp = FuzzyDateTime(start_dt=datetime(2000, 1, 1, tzinfo=timezone.utc))


class EpisodeDetailsFactory(Factory):
    class Meta:
        model = EpisodeDetails

    show_title = Faker('name')
    download = SubFactory(DownloadFactory, type='EPISODE')

    season = Faker('numerify', text='#')
    episode = Faker('numerify', text='#')


class MovieDetailsFactory(Factory):
    class Meta:
        model = MovieDetails

    download = SubFactory(DownloadFactory, type='MOVIE')
