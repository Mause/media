import json
from typing import Annotated, AsyncGenerator, Callable

import aiohttp
from healthcheck import HealthcheckCallbackResponse, HealthcheckStatus
from pydantic import BaseModel, ConfigDict, Field

from .abc import ImdbId, ITorrent, MovieProvider, ProviderSource, TmdbId

url = "http://luna-leederville.3cx.com.au:4025/VenueSchedule.json"


def mk(prefix: str) -> Callable[[str], str]:
    def to_title(s: str) -> str:
        return prefix + s.title()

    return to_title


class Base(BaseModel):
    model_config = ConfigDict(
        alias_generator=mk(''),
        populate_by_name=True,
        populate_by_alias=True,
    )


class Movie(Base):
    model_config = ConfigDict(
        alias_generator=mk("Movie_"),
    )
    name: str
    imdb_id: Annotated[str | None, Field(alias='Movie_IMDB_ID')]
    tmdb_id: Annotated[str | None, Field(alias='Movie_TMDb_ID')]

    url: Annotated[str, Field(alias='Movie_URL')]
    code: str


class Session(Base):
    model_config = ConfigDict(
        alias_generator=mk("Session_"),
    )
    index: int


class Schedule(Base):
    sessions: list[Session]
    movies: list[Movie]


async def get_venue_schedule() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json(content_type=None, encoding='utf-16-le')


class LunaProvider(MovieProvider):
    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        schedule = await get_venue_schedule()
        for item in schedule['Items']:
            title = item['Title']
            yield ITorrent(
                title=title,
                source=ProviderSource.LUNA,
                seeders=1,
                download=f"http://luna-leederville.3cx.com.au:4025/Download/{item['Id']}",
                category="Movie",
            )

    async def health(self) -> HealthcheckCallbackResponse:
        await get_venue_schedule()
        return HealthcheckCallbackResponse(HealthcheckStatus.PASS, "OK")


async def main() -> None:
    with open('luna_venue_schedule.json', 'r') as f:
        Schedule.model_validate_json(f.read())

    schedule = await get_venue_schedule()

    with open('luna_venue_schedule.json', 'w') as f:
        json.dump(schedule, f, indent=2)


if __name__ == "__main__":
    import uvloop

    uvloop.run(main())
