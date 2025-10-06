from collections.abc import AsyncGenerator

from healthcheck import HealthcheckCallbackResponse, HealthcheckStatus

from attractive import search_yts  # type: ignore[attr-defined]

from ..types import ImdbId, TmdbId
from .abc import ITorrent, MovieProvider, ProviderSource


class YtsProvider(MovieProvider):
    type = ProviderSource.YTS

    async def search_for_movie(
        self,
        imdb_id: ImdbId,
        tmdb_id: TmdbId,
    ) -> AsyncGenerator[ITorrent, None]:
        for torrent in await search_yts(imdb_id):
            yield ITorrent(
                seeders=torrent.seeders,
                source=ProviderSource.YTS,
                title=torrent.title,
                category=torrent.category,
                download=torrent.magnet,
            )

    async def health(self) -> HealthcheckCallbackResponse:
        return HealthcheckCallbackResponse(
            output="YtsProvider is healthy",
            status=HealthcheckStatus.PASS,
        )
