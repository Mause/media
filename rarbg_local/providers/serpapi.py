from datetime import datetime, timezone

import aiohttp
import geoip2.database
import geoip_api
from geoip_api.core.lookup import get_database_path


async def search(movie_name: str, location: str, iso_code: str, api_key: str) -> dict:
    async with aiohttp.ClientSession() as session:
        res = await session.get(
            'https://serpapi.com/search.json',
            params={
                'q': f'{movie_name} show times',
                'location': location,
                'hl': 'en',
                'gl': iso_code,
                'api_key': api_key,
            },
        )
        res.raise_for_status()
        return await res.json()


def resolve_location(ip_address: str) -> dict:
    api = geoip_api.GeoIPLookup(download_if_missing=True)

    return api.lookup(ip_address)


def get_age() -> datetime:
    with geoip2.database.Reader(get_database_path()) as city_reader:
        m = city_reader.metadata()
        return datetime.fromtimestamp(m.build_epoch, timezone.utc)
