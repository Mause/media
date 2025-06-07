from aiohttp import ClientSession
from cachetools import TTLCache
from fuzzywuzzy import fuzz

from .tmdb import get_tv
from .utils import cached


def make_jikan() -> ClientSession:
    return ClientSession(base_url='https://api.jikan.moe/v4/')


@cached(TTLCache(256, 360))
async def get_names(tmdb_id: int) -> set[str]:
    tv = await get_tv(tmdb_id)
    async with make_jikan() as jikan:
        res = await jikan.get('anime', params={'q': tv.name, 'limit': 1})
        results = (await res.json())['data']
        if not results:
            return {tv.name}

        result = results[0]
        if closeness(tv.name, [result['title']]) < 95:
            return {tv.name}

        return set([tv.name, result['title']] + result['title_synonyms'])


def closeness(key: str, names: list[str]) -> int:
    return max(fuzz.ratio(key.lower(), name.lower()) for name in names)
