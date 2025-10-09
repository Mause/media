import json
import logging
from collections.abc import AsyncGenerator, Callable, Generator
from datetime import datetime, timezone
from os.path import exists
from typing import Annotated, cast

import aiohttp
from aiocache.base import BaseCache
from fastapi import Request
from healthcheck import HealthcheckCallbackResponse, HealthcheckStatus
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer
from pydantic.types import AwareDatetime

from ..cache import get_cache
from ..singleton import get, request_var
from .abc import ImdbId, ITorrent, MovieProvider, ProviderSource, TmdbId

logger = logging.getLogger(__name__)
fmt = "%Y%m%dT%H%M%S"
url = "http://luna-leederville.3cx.com.au:4025/VenueSchedule.json"
LUNA_SCHEDULE = 'luna-schedule'


def mk(prefix: str) -> Callable[[str], str]:
    def to_title(s: str) -> str:
        return prefix + s.title()

    return to_title


class Base(BaseModel):
    model_config = ConfigDict(
        alias_generator=mk(''),
        validate_by_name=True,
        validate_by_alias=True,
    )


class Movie(Base):
    model_config = ConfigDict(
        alias_generator=mk("Movie_"),
    )
    name: str
    imdb_id: Annotated[ImdbId | None, Field(alias='Movie_IMDB_ID')]
    tmdb_id: Annotated[TmdbId | None, Field(alias='Movie_TMDb_ID')]

    url: Annotated[str, Field(alias='Movie_URL')]
    code: str


WeirdDateTime = Annotated[
    AwareDatetime,
    BeforeValidator(lambda x: datetime.strptime(x, fmt).astimezone(tz=timezone.utc)),
    PlainSerializer(lambda x: x.strftime(fmt)),
]


class Session(Base):
    model_config = ConfigDict(
        alias_generator=mk("Session_"),
    )
    index: int
    movie_code: str
    url: Annotated[str, Field(alias='Session_URL')]
    date_time: WeirdDateTime
    end_time: WeirdDateTime


class Schedule(Base):
    sessions: list[Session]
    movies: list[Movie]


async def get_raw() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json(content_type=None, encoding='utf-16-le')


async def get_venue_schedule() -> Schedule:
    request = request_var.get()
    assert isinstance(request, Request)

    cache = cast(BaseCache, await get(request.app, get_cache, request))
    assert isinstance(cache, BaseCache), cache

    luna = await cache.get(LUNA_SCHEDULE)
    if luna:
        return Schedule.model_validate(luna)

    luna = await get_raw()
    await cache.set(LUNA_SCHEDULE, luna, ttl=360)
    return Schedule.model_validate(luna)


class LunaProvider(MovieProvider):
    type = ProviderSource.LUNA

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        schedule = await get_venue_schedule()
        for item in self.process(schedule, imdb_id, tmdb_id):
            yield item

    def process(
        self, schedule: Schedule, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> Generator[ITorrent, None, None]:
        movie = next(
            (
                m
                for m in schedule.movies
                if m.imdb_id == imdb_id or m.tmdb_id == tmdb_id
            ),
            None,
        )
        if not movie:
            return
        for session in schedule.sessions:
            if session.movie_code != movie.code:
                continue
            yield ITorrent(
                title=f"{movie.name} - Session {session.index}",
                source=ProviderSource.LUNA,
                seeders=1,
                download=session.url,
                category="Movie",
            )

    async def health(self) -> HealthcheckCallbackResponse:
        await get_venue_schedule()
        return HealthcheckCallbackResponse(HealthcheckStatus.PASS, "OK")


async def main() -> None:
    filename = 'luna_venue_schedule.json'

    if exists(filename):
        with open(filename) as f:
            schedule = Schedule.model_validate_json(f.read())
            prov = LunaProvider()
            for torrent in prov.process(
                schedule, imdb_id=ImdbId('tt31176520'), tmdb_id=TmdbId(648878)
            ):
                logger.info('Luna: %s', torrent)

    else:
        raw_schedule = await get_raw()

        with open(filename, 'w') as f:
            json.dump(raw_schedule, f, indent=2)


if __name__ == "__main__":
    import uvloop

    uvloop.run(main())
