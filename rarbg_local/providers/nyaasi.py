from collections.abc import AsyncGenerator

from fastapi.concurrency import run_in_threadpool
from nyaapy.nyaasi.nyaa import Nyaa
from sentry_sdk import trace

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..tmdb import get_tv
from ..types import ImdbId, TmdbId
from .abc import TvProvider, format, tv_convert


class NyaaProvider(TvProvider):
    type = ProviderSource.NYAA_SI

    async def search_for_tv(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
        season: int,
        episode: int | None = None,
    ) -> AsyncGenerator[ITorrent, None]:
        ny = Nyaa()

        name = (await get_tv(tmdb_id)).name
        page = 0
        template = f'{name} ' + format(season, episode)

        def search():
            return trace(ny.search)(keyword=template, page=page)

        while True:
            items = await run_in_threadpool(search)
            if items:
                page += 1
            else:
                break

            for item in items:
                yield ITorrent(
                    source=ProviderSource.NYAA_SI,
                    title=item.name,
                    seeders=item.seeders,
                    download=item.magnet,
                    category=tv_convert(item.category),
                    episode_info=EpisodeInfo(seasonnum=season, epnum=episode),
                )

    async def health(self):
        return await self.check_http('https://nyaa.si')
