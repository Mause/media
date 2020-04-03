from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dataclasses_json import DataClassJsonMixin

CONVERT = {
    '720': 'TV Episodes',
    '720p': 'TV Episodes',
    '1080': 'TV HD Episodes',
    '1080p': 'TV HD Episodes',
    'x264': 'TV HD Episodes',
}


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

    def __post_init__(self):
        if self.category not in CONVERT.values():
            self.category = CONVERT[self.category]
