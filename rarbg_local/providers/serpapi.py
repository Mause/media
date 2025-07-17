import aiohttp
import geoip_api


async def search(movie_name: str, location: str, api_key: str) -> dict:
    async with aiohttp.ClientSession() as session:
        res = await session.get(
            'https://serpapi.com/search.json',
            params={
                'q': f'{movie_name} show times',
                'location': 'Austin, Texas, United States',
                'hl': 'en',
                'gl': 'us',
                'apiKey': api_key,
            },
        )
        res.raise_for_status()
        return await res.json()


def resolve_location(ip_address: str) -> str:
    api = geoip_api.GeoIPLookup(download_if_missing=True)

    return str(api.lookup(ip_address))
