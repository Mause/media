from .abc import MovieProvider


class TorrentsCsvProvider(MovieProvider):
    name = "torrentscsv"
    type = ProviderSource.TORRENTS_CSV

    async def search_for_movie(
        self, imdb_id: str, tmdb_id: int
    ) -> AsyncGenerator[ITorrent, None]:
        async with aiohttp.ClientSession() as session:
            res = await session.get(
                "https://torrents-csv.com/service/search", params={"q": imdb_id}
            )
            for item in (await res.json())['torrents']:
                yield ITorrent(
                    source=ProviderSource.TORRENTS_CSV,
                    title=item['name'],
                    seeders=item['seeders'],
                    download=item['infohash'],
                )
