import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice

from ..db import Download, EpisodeDetails
from ..models import (
    DownloadAllResponse,
    Episode,
    EpisodeInfo,
    ITorrent,
    ProviderSource,
    TvSeasonResponse,
)


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


class DownloadFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Download
        sqlalchemy_session = True


class EpisodeDetailsFactory(SQLAlchemyModelFactory):
    class Meta:
        model = EpisodeDetails

        sqlalchemy_session = True

    show_title = factory.Faker('name')
    download = factory.SubFactory(DownloadFactory)
