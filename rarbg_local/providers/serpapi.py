import aiohttp


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
