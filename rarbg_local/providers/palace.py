'''
https://prod-api.palace-cinemas.workers.dev/banner?displayLocation=restOfSite&locality=melbourne
https://prod-api.palace-cinemas.workers.dev/cinemas
https://prod-api.palace-cinemas.workers.dev/cinemas?platinum=true
https://prod-api.palace-cinemas.workers.dev/engagement
https://prod-api.palace-cinemas.workers.dev/menu
https://prod-api.palace-cinemas.workers.dev/movies?locality=melbourne
https://prod-api.palace-cinemas.workers.dev/movies/now/trending?locality=melbourne
https://prod-api.palace-cinemas.workers.dev/movies/the-phoenician-scheme?locality=melbourne&isPreviewMode=null
https://prod-api.palace-cinemas.workers.dev/sessions/combo-box-items
https://prod-api.palace-cinemas.workers.dev/sessions/date-items
.get("/account/details", {
.get("/account/details/navbar", {
.get("/account/details/preferences", {
.get("/account/options")
.get("/account/rewards", {
.get("/home-featured?locality=".concat(e))
.get("/home?locality=".concat(t, "&isPreviewMode=").concat(n))
.get("/media/".concat(e))
.get("/menu", {
.get("/movies?locality=".concat(e), {
.get("/movies/byid/".concat(e))
.get("/movies/now/trending?locality=".concat(e))
.get("/popup/?locality=".concat(e))
.get("/search?q=".concat(encodeURIComponent(e)))
.get("/sessions/alert-banners?selectedCinemaIds=".concat(e.join(",")), {
.get("/sessions/quickbook/".concat(e, "/").concat(t))
.get("/sessions/quickbook/".concat(e))
'''

from collections.abc import AsyncGenerator
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Annotated, Any, Literal, NewType

import aiohttp
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    RootModel,
    ValidatorFunctionWrapHandler,
)
from pydantic.alias_generators import to_camel, to_pascal
from pydantic_core import CoreSchema, core_schema
from pydantic_extra_types.color import Color
from pydantic_extra_types.coordinate import Latitude, Longitude
from rich import print
from uritemplate import URITemplate

from .abc import ImdbId, ITorrent, MovieProvider, ProviderSource, TmdbId

CinemaId = NewType('CinemaId', str)
SessionId = NewType('SessionId', str)
MovieId = NewType('MovieId', str)
MovieSlug = NewType('MovieSlug', str)


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
            'Special Event',
        ]
    ]
    no_free_tickets: bool
    audio_description: bool
    close_caption: bool
    display_attribute_colour: Color | None
    display_attribute_text: str | None
    is_platinum: bool
    sale_status: Literal['Selling Fast', 'Sold Out'] | None
    session_id: SessionId
    cinema_id: CinemaId
    is_special_event: bool


class BaseMovie(Shared):
    movie_id: MovieId
    title: str
    slug: MovieSlug
    trailer_url: str
    synopsis: str | None
    rating: str
    release_date_utc: datetime


class Review(Shared):
    id: str
    content: str
    rating: str | None
    reviewer: str


class Person(Shared):
    model_config = ConfigDict(alias_generator=to_pascal)
    id: Annotated[str, Field(alias='ID')]
    first_name: str
    last_name: str
    person_type: Literal['Director', 'Cast', 'Actor']
    url_to_picture: str | None
    url_to_details: str | None


class ParticipatingCinema(Shared):
    slug: str
    title: str


class Paragraph(Shared):
    version: Literal[1]
    type: Literal['paragraph']
    direction: Literal['ltr'] | None = None
    children: list['Node']
    indent: Literal[0]
    format: Literal['', 'start']


class Text(Shared):
    type: Literal['text']
    detail: Literal[0]
    format: Literal[0, 1, 2, 3]
    text: str
    mode: Literal['normal']
    version: Literal[1]
    style: Literal['']


class Heading(Shared):
    type: Literal['heading']
    tag: Literal['h2', 'h3', 'h6']

    direction: Literal['ltr'] | None
    children: list['Node']
    indent: Literal[0]
    version: Literal[1]
    format: Literal['', 'start']


class LinkFields(Shared):
    new_tab: bool
    link_type: Literal['custom']
    doc: None
    url: str


class Link(Shared):
    type: Literal['link']

    format: Literal['']
    direction: Literal['ltr'] | None
    children: list['Node']
    version: Literal[1]
    indent: Literal[0]
    fields: LinkFields


class Node(
    RootModel[Annotated[Paragraph | Text | Heading | Link, Field(discriminator='type')]]
):
    pass


class Root(Shared):
    type: Literal['root']
    direction: Literal['ltr'] | None
    children: list[Node] | None = None
    version: Literal[1]
    indent: int | None = None
    format: Literal['']


class AdditionalDetail(Shared):
    root: Root


class SingleMovie(BaseMovie):
    awards: list[int]
    meta_title: str
    meta_description: str | None
    meta_json_ld: object
    meta_image: str

    logo_alt: str
    logo_max_height: int | None
    logo_max_width: int
    logo_mobile_max_height: int
    logo_top_mobile_spacing: int | None
    logo: str

    participating_cinemas: list[ParticipatingCinema]
    media_inserts: list[int]
    hero_image: str
    hero_image_alt: str
    reviews: list[Review]

    accent_colour: Color
    is_alt_content: bool
    is_repertory: bool
    is_arts_on_screen: bool
    additional_detail: AdditionalDetail | None
    short_synopsis: str
    html_content: str | None
    genre_name: list[str]
    genre_id: list[str]
    cast: list[Person]
    run_time: Annotated[timedelta, HumanTimeDelta()]
    language: str | None
    director: list[Person]


class Movie(BaseMovie):
    now_showing_order: int | None
    genre_names: list[str]

    sessions: list[Session]


class Cinema(Shared):
    cinema_id: CinemaId
    order: int | None

    short_name: str
    title: str

    region: str
    slug: str
    movio_id: str

    card_image: str
    card_alt: str

    nearby_cinema_ids: list[CinemaId] = []

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


class MovieOrderType(Enum):
    MOVIE_NAME = 'MOVIE_NAME'
    RECOMMENDED = 'RECOMMENDED'
    NEWEST_RELEASE = 'NEWEST_RELEASE'


class FilterArgs(Shared):
    selected_cinema_ids: list[CinemaId] = []
    selected_dates: list[date] | None = None
    modern_view: bool = True
    movie_order_type: MovieOrderType = MovieOrderType.MOVIE_NAME
    new_release: bool = False
    special_event: bool = False
    film_festival: bool = False
    family: bool = False
    retro: bool = False
    art_to_screen: bool = False
    selected_movie_slug: MovieSlug | None = None


async def get_sessions_date_items(
    session: aiohttp.ClientSession, filter_args: FilterArgs
) -> list[date]:
    res = await session.post(
        "/sessions/date-items", json=filter_args.model_dump(mode='json')
    )
    res.raise_for_status()
    return RootModel[list[date]].model_validate(await res.json()).root


class ComboBoxItem(Shared):
    movie_slug: MovieSlug
    title: str


async def get_sessions_combo_box_items(
    session: aiohttp.ClientSession, filter_args: FilterArgs
) -> list[ComboBoxItem]:
    res = await session.post(
        "/sessions/combo-box-items", json=filter_args.model_dump(mode='json')
    )
    res.raise_for_status()
    return RootModel[list[ComboBoxItem]].model_validate(await res.json()).root


async def get_sessions_disabled_cinemas(
    session: aiohttp.ClientSession, filter_args: FilterArgs
) -> list[CinemaId]:
    res = await session.post(
        "/sessions/disabled-cinemas", json=filter_args.model_dump(mode='json')
    )
    res.raise_for_status()
    return RootModel[list[CinemaId]].model_validate(await res.json()).root


async def get_cinemas(session: aiohttp.ClientSession) -> list[Cinema]:
    res = await session.get(
        '/cinemas',
        params=to_params({'platinum': False}),
    )
    res.raise_for_status()
    return RootModel[list[Cinema]].model_validate(await res.json()).root


async def get_movie_by_slug(
    session: aiohttp.ClientSession, slug: MovieSlug
) -> SingleMovie:
    res = await session.get(
        URITemplate("/movies/{slug}").expand(slug=slug),
        params={'locality': 'melbourne', 'isPreviewMode': 'null'},
    )
    res.raise_for_status()
    return RootModel[SingleMovie].model_validate(await res.json()).root


async def get_movie_by_id(
    session: aiohttp.ClientSession, ident: MovieId
) -> SingleMovie:
    res = await session.get(URITemplate("/movies/byid/{ident}").expand(ident=ident))
    res.raise_for_status()
    return RootModel[SingleMovie].model_validate(await res.json()).root


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


class BaseSearchResult(Shared):
    type: str


class EventSearchResult(BaseSearchResult):
    type: Literal["events"]
    slug: str
    title: str
    filename: str
    content: AdditionalDetail | str
    herotext: str | None
    caption: str


class MovieSearchResult(BaseSearchResult):
    type: Literal["movies"]
    slug: str
    title: str
    content: str | None
    id: MovieId
    caption: str


class CinemasSearchResult(BaseSearchResult):
    type: Literal['cinemas']
    id: str
    slug: str
    title: str
    filename: str
    caption: str
    content: AdditionalDetail | str
    json_: Annotated[bool, Field(name='json', alias='json')]


class OffersSearchResult(BaseSearchResult):
    type: Literal['offers']
    herotext: str | None = None
    id: int
    slug: str
    title: str
    caption: str
    filename: str
    json_: Annotated[bool, Field(name='json', alias='json')]
    content: AdditionalDetail | str


class SearchResult(
    RootModel[
        Annotated[
            MovieSearchResult
            | EventSearchResult
            | CinemasSearchResult
            | OffersSearchResult,
            Field(discriminator='type'),
        ]
    ]
):
    pass


async def search(session: aiohttp.ClientSession, query: str) -> list[SearchResult]:
    res = await session.get('/search', params={'q': query})
    res.raise_for_status()
    return RootModel[list[SearchResult]].model_validate(await res.json()).root


class PalaceProvider(MovieProvider):
    type = ProviderSource.PALACE

    async def search_for_movie(
        self, imdb_id: ImdbId, tmdb_id: TmdbId
    ) -> AsyncGenerator[ITorrent, None]:
        if not True:
            yield


async def main() -> None:
    session = aiohttp.ClientSession(
        base_url="https://prod-api.palace-cinemas.workers.dev",
    )

    async with session:
        session_date_items = await get_sessions_date_items(
            session,
            FilterArgs(
                selected_dates=[date.today() + timedelta(days=i) for i in range(7)],
            ),
        )

        cinemas = await get_cinemas(session)
        print(cinemas)
        ids = [c.cinema_id for c in cinemas]
        assert session_date_items[0:2]
        sessions = await get_sessions(
            session,
            filter_args=FilterArgs(
                selected_cinema_ids=ids,
                selected_dates=session_date_items[0:2],
                # selected_movie_slug='f1-the-movie',
            ),
        )
        print(sessions)

        for movie in sessions.data:
            await get_movie_by_slug(session, movie.slug)
            # await get_movie_by_id(session, movie_session.session_id)


if __name__ == '__main__':
    import uvloop

    uvloop.run(main())
