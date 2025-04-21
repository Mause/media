from typing import Set

from aiohttp import ClientSession
from cachetools import TTLCache
from fuzzywuzzy import fuzz

from .tmdb import get_tv
from .utils import cached


def make_jikan():
    return ClientSession(base_url='https://api.jikan.moe/v3/')


@cached(TTLCache(256, 360))
async def get_names(tmdb_id: int) -> Set[str]:
    tv = await get_tv(tmdb_id)
    async with make_jikan() as jikan:
        res = await jikan.get('search/anime', params={'q': tv.name, 'limit': 1})
        results = (await res.json())['results']
        if not results:
            return {tv.name}

        result = results[0]
        if closeness(tv.name, [result['title']]) < 95:
            return {tv.name}

        result = await (await jikan.get(f'anime/{results[0]["mal_id"]}')).json()

        return set([tv.name, result['title']] + result['title_synonyms'])


def closeness(key, names):
    return max(fuzz.ratio(key.lower(), name.lower()) for name in names)
