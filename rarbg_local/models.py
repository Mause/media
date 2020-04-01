from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin

CONVERT = {'720': 'x264/720', '1080': 'x264/1080', 'x264': 'x264/1080'}


@dataclass
class EpisodeInfo(DataClassJsonMixin):
    seasonnum: Optional[str]
    epnum: Optional[str]


@dataclass
class ITorrent(DataClassJsonMixin):
    source: str
    title: str
    seeders: int
    download: str
    category: str
    episode_info: EpisodeInfo

    def __post_init__(self):
        self.category = CONVERT[self.category]
