from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin


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
