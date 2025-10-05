import logging
from collections import ChainMap
from collections.abc import AsyncGenerator
from typing import Annotated, Literal, Union

from fastapi import APIRouter, WebSocket
from fastapi.requests import Request
from pydantic import BaseModel, Field, RootModel, SecretStr, ValidationError

from .auth import security
from .db import (
    User,
)
from .models import ITorrent, PlexMedia, PlexResponse
from .plex import get_imdb_in_plex, get_plex
from .providers import (
    search_for_movie,
    search_for_tv,
)
from .singleton import get
from .tmdb import ThingType, get_movie_imdb_id, get_tv_imdb_id
from .types import TmdbId
from .utils import Message, non_null

logger = logging.getLogger(__name__)

websocket_ns = APIRouter()


StreamType = Literal['series', 'movie']


class BaseRequest(BaseModel):
    request_type: str
    authorization: SecretStr


class StreamArgs(BaseRequest):
    request_type: Literal['stream']

    type: StreamType
    tmdb_id: TmdbId
    season: int | None = None
    episode: int | None = None


class PingArgs(BaseRequest):
    request_type: Literal['ping']


class PlexArgs(BaseRequest):
    request_type: Literal['plex']
    tmdb_id: TmdbId
    media_type: ThingType


class Reqs(
    RootModel[
        Annotated[
            Union[StreamArgs, PingArgs, PlexArgs],
            Field(discriminator='request_type'),
        ]
    ]
):
    pass


async def _stream(
    type: StreamType,
    tmdb_id: TmdbId,
    season: int | None = None,
    episode: int | None = None,
) -> AsyncGenerator[ITorrent]:
    if type == 'series':
        tasks, queue = await search_for_tv(
            await get_tv_imdb_id(tmdb_id), tmdb_id, non_null(season), episode
        )
    else:
        tasks, queue = await search_for_movie(await get_movie_imdb_id(tmdb_id), tmdb_id)

    while not all(task.done() for task in tasks):
        item = await queue.get()
        if isinstance(item, Message):
            logger.info('Message from provider: %s', item)
        else:
            yield item


def make_request(websocket: WebSocket, request: BaseRequest) -> Request:
    return Request(
        scope=ChainMap(
            {
                'type': 'http',
                'headers': [
                    (
                        b"authorization",
                        (request.authorization.get_secret_value()).encode(),
                    ),
                ],
            },
            websocket.scope,
        ),
        receive=websocket.receive,
        send=websocket.send,
    )


async def authenticate(websocket: WebSocket, request: BaseRequest) -> User:
    def fake(user: Annotated[User, security]) -> User:
        return user

    try:
        user = await get(
            websocket.app,
            fake,
            make_request(websocket, request),
        )
    except Exception as e:
        logger.exception('Unable to authenticate websocket request')
        await close(websocket, e)
        raise

    logger.info('Authed user: %s', user)

    return user


async def close(websocket: WebSocket, e: Exception) -> None:
    name = type(e).__name__
    message: dict[str, object] = {'error': str(e), 'type': name}
    if isinstance(e, ValidationError):
        message.update(
            {
                'error': f'{e.error_count()} validation errors for {e.title}',
                'errors': e.errors(),
            }
        )
    await websocket.send_json(message)
    await websocket.close(reason=name)


class PlexRootResponse(RootModel[dict[str, PlexResponse[PlexMedia]]]):
    pass


@websocket_ns.websocket("/ws")
async def websocket_stream(websocket: WebSocket) -> None:
    logger.info('Got websocket connection')
    await websocket.accept()

    try:
        request = Reqs.model_validate(await websocket.receive_json()).root
    except ValidationError as e:
        return await close(websocket, e)

    logger.info('Got request: %s', request)

    await authenticate(websocket, request)

    message = 'No message provided'

    if request.request_type == 'stream':
        async for item in _stream(
            type=request.type,
            tmdb_id=request.tmdb_id,
            season=request.season,
            episode=request.episode,
        ):
            await websocket.send_json(item.model_dump(mode='json'))

        message = 'Finished streaming'
    elif request.request_type == 'ping':
        message = 'Pong'
    elif request.request_type == 'plex':
        plex = await get(websocket.app, get_plex, make_request(websocket, request))
        # plex = await gracefully_get_plex(request, settings)
        dat = await get_imdb_in_plex(request.media_type, request.tmdb_id, plex)

        if not dat:
            return await close(websocket, Exception('Not found in plex'))

        await websocket.send_json(
            PlexRootResponse.model_validate(
                {
                    key: PlexResponse[PlexMedia](
                        item=PlexMedia.model_validate(value),
                        server_id=plex.machineIdentifier,
                    )
                    if value
                    else None
                    for key, value in dat.items()
                }
            ).model_dump(mode='json')
        )

        message = 'Plex complete'
    else:
        return await close(websocket, Exception('No such method'))

    logger.info(message)
    await websocket.close(reason=message)
