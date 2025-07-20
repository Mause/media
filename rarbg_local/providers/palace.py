from datetime import date, datetime, timedelta
from typing import Annotated, Any, Literal

import aiohttp
from pydantic import (
    BaseModel,
    ConfigDict,
    GetCoreSchemaHandler,
    RootModel,
    ValidatorFunctionWrapHandler,
)
from pydantic.alias_generators import to_camel
from pydantic_core import CoreSchema, core_schema
from pydantic_extra_types.color import Color
from pydantic_extra_types.coordinate import Latitude, Longitude


class HumanTimeDelta:
    def tz_constraint_validator(
        self, value: str, handler: ValidatorFunctionWrapHandler
    ) -> Any:
        parts = value.split()
        assert len(parts) == 2
        assert parts[1] == 'MIN'
        return handler(timedelta(minutes=int(parts[0])))

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.tz_constraint_validator,
            handler(source_type),
        )


class Page[T](BaseModel):
    data: list[T] = []
    page: int = 1
    items_per_page: int = 6
    total_pages: int = 0
    total_items: int = 0


class Shared(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        alias_generator=to_camel,
        serialize_by_alias=True,
        validate_by_name=True,
        validate_by_alias=True,
    )


class Session(Shared):
    date: datetime
    session_info: list[
        Literal[
            'Hearing Impaired',
            'Closed Captioning Available',
            'All seats recline',
            'No Free Tickets',
            'Audio Description Session',
        ]
    ]
    no_free_tickets: bool
    audio_description: bool
    close_caption: bool
    display_attribute_colour: Color | None
    display_attribute_text: str | None
    is_platinum: bool
    sale_status: Literal['Selling Fast'] | None
    session_id: str
    cinema_id: str
    is_special_event: bool


class Movie(Shared):
    language: str | None
    now_showing_order: int | None
    release_date_utc: datetime
    genre_names: list[str]
    run_time: Annotated[timedelta, HumanTimeDelta()]
    synopsis: str | None
    trailer_url: str
    rating: str
    title: str
    movie_id: str
    slug: str

    sessions: list[Session]


class Cinema(Shared):
    cinema_id: str
    order: int | None

    short_name: str
    title: str

    region: str
    slug: str
    movio_id: str

    card_image: str
    card_alt: str

    nearby_cinema_ids: list[str] = []

    longitude: Longitude
    latitude: Latitude
    locality: Literal[
        'melbourne',
        'sydney',
        'canberra',
        'brisbane',
        'ballarat',
        'byronBay',
        'perth',
    ]
    locality_display_name: str
    is_platinum: bool
    street: str
    city: str


def to_params(value: dict) -> dict:
    def single(v: Any) -> Any:
        if isinstance(v, bool):
            return 'true' if v else 'false'
        elif isinstance(v, list):
            return ','.join(v)
        return v

    return {k: single(v) for k, v in value.items() if v is not None}


class FilterArgs(Shared):
    selected_cinema_ids: list[str] = []
    selected_dates: list[date] | None = None
    modern_view: bool = True
    movie_order_type: Literal['MOVIE_NAME'] = 'MOVIE_NAME'
    new_release: bool = False
    special_event: bool = False
    film_festival: bool = False
    family: bool = False
    retro: bool = False
    art_to_screen: bool = False
    selected_movie_slug: str | None = None


async def get_sessions_date_items(
    session: aiohttp.ClientSession, filter_args: FilterArgs
) -> list[date]:
    res = await session.post(
        "/sessions/date-items", json=filter_args.model_dump(mode='json')
    )
    res.raise_for_status()
    return RootModel[list[date]].model_validate(await res.json()).root


async def get_cinemas(session: aiohttp.ClientSession) -> list[Cinema]:
    res = await session.get(
        '/cinemas',
        params=to_params({'platinum': False}),
    )
    res.raise_for_status()
    return RootModel[list[Cinema]].model_validate(await res.json()).root


async def get_sessions(
    session: aiohttp.ClientSession,
    *,
    filter_args: FilterArgs,
) -> Page[Movie]:
    res = await session.get(
        '/sessions',
        params=to_params(
            {
                'page': 1,
                **filter_args.model_dump(mode='json'),
            }
        ),
    )
    res.raise_for_status()
    return Page[Movie].model_validate(await res.json())
