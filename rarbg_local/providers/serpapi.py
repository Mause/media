import json
from datetime import datetime
from typing import Annotated, Any

import aiohttp
from fastapi import Request
from pydantic import BaseModel, GetCoreSchemaHandler, ValidatorFunctionWrapHandler
from pydantic_core import CoreSchema, core_schema
from rich import print

from .geolocate import resolve_location


class HumanDate:
    def tz_constraint_validator(
        self, value: str, handler: ValidatorFunctionWrapHandler
    ) -> Any:
        '''
        Parses strings of the format "March 31, 1999 (USA)"
        '''
        value = value.split('(')[0].strip()
        return handler(datetime.strptime(value, '%B %d, %Y').date())

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.tz_constraint_validator,
            handler(source_type),
        )


class Showtime(BaseModel):
    title: str
    theater: str
    time: datetime
    url: str


class KnowledgeGraph(BaseModel):
    title: str
    description: str
    # image: str
    # url: str
    rating: float | None = None
    rating_count: int | None = None
    release_date: Annotated[datetime | None, HumanDate()] = None
    director: list[str] = []
    actors: list[str] = []
    genres: list[str] = []


class SearchResult(BaseModel):
    showtimes: list[Showtime] = []
    knowledge_graph: KnowledgeGraph | None = None


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
        js = await res.json()
        res.raise_for_status()
        return js


async def main() -> None:
    import os

    import dotenv

    with open('data.json') as fh:
        data = SearchResult.model_validate_json(fh.read())

    print(data)

    dotenv.load_dotenv()

    ip_address = '203.12.14.33'
    location = resolve_location(Request(scope={'client': (ip_address.encode(), 0)}))
    assert location is not None, 'Could not resolve location'

    movie_name = 'The Phoenician Scheme'
    js = await search(
        movie_name=movie_name,
        location=', '.join(
            [
                part
                for part in (
                    location.city.name,
                    location.subdivisions.most_specific.name,
                    location.country.name,
                )
                if part
            ]
        ),
        iso_code=location.country.iso_code or 'au',
        api_key=os.environ['SERP_API_KEY'],
    )
    with open(f'{movie_name}.json', 'w') as fh:
        json.dump(js, fh, indent=2)


if __name__ == '__main__':
    import uvloop

    uvloop.run(main())
