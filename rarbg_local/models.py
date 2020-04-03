from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dataclasses_json import DataClassJsonMixin


class ProviderSource(Enum):
    KICKASS = 'KICKASS'
    HORRIBLESUBS = 'HORRIBLESUBS'
    RARBG = 'RARBG'


@dataclass
class EpisodeInfo(DataClassJsonMixin):
    seasonnum: Optional[str]
    epnum: Optional[str]


@dataclass
class ITorrent(DataClassJsonMixin):
    source: ProviderSource
    title: str
    seeders: int
    download: str
    category: str
    episode_info: EpisodeInfo
