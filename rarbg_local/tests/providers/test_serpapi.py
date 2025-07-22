import json
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from aioresponses import aioresponses as Aioresponses
from pydantic import ValidatorFunctionWrapHandler
from pytest import mark

from ...providers.serpapi import HumanDate, search
from ..conftest import add_json


class Handler(ValidatorFunctionWrapHandler):
    def __call__(self, a: Any, b: str | int | None = None) -> Any:
        return a


def test_human_date() -> None:
    hd = HumanDate()
    value = "March 31, 1999 (USA)"
    assert hd.tz_constraint_validator(value, Handler()) == date(1999, 3, 31)


@mark.asyncio
@mark.skip
async def test_serpapi(resource_path: Path, aioresponses: Aioresponses) -> None:
    args = {
        "api_key": "test",
        "gl": "au",
        "hl": "en",
        "location": "Sydney, Australia",
        "q": "The Matrix show times",
    }
    add_json(
        aioresponses,
        method='GET',
        url="https://serpapi.com/search.json?" + urlencode(args),
        json_body=json.load((resource_path / "serpapi.json").open()),
    )

    await search(
        movie_name="The Matrix",
        api_key="test",
        iso_code="au",
        location="Sydney, Australia",
    )
