import json
from typing import AsyncGenerator

import aiohttp
from healthcheck import HealthcheckCallbackResponse, HealthcheckStatus

from .abc import ITorrent, MovieProvider, ProviderSource

url = "http://luna-leederville.3cx.com.au:4025/VenueSchedule.json"


async def get_venue_schedule() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json(content_type=None, encoding='utf-16-le')


class LunaProvider(MovieProvider):
    async def search_for_movie(self) -> AsyncGenerator[ITorrent, None]:
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
    schedule = await get_venue_schedule()

    with open('luna_venue_schedule.json', 'w') as f:
        json.dump(schedule, f, indent=2)


if __name__ == "__main__":
    import uvloop

    uvloop.run(main())
