from aiohttp import ClientSession
from cachetools import TTLCache
from fuzzywuzzy import fuzz

from .tmdb import TmdbAPI
from .utils import cached


def make_jikan():
    return ClientSession(base_url='https://api.jikan.moe/v4/')


@cached(TTLCache(256, 360))
async def get_names(tmdb: TmdbAPI, tmdb_id: int) -> set[str]:
    tv = await tmdb.get_tv(tmdb_id)
    async with make_jikan() as jikan:
        res = await jikan.get('anime', params={'q': tv.name, 'limit': 1})
        results = (await res.json())['data']
        if not results:
            return {tv.name}

        result = results[0]
        if closeness(tv.name, [result['title']]) < 95:
            return {tv.name}

        return set([tv.name, result['title']] + result['title_synonyms'])


def closeness(key, names):
    return max(fuzz.ratio(key.lower(), name.lower()) for name in names)
