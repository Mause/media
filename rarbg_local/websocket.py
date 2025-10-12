import logging
import time
from asyncio import create_task, sleep
from collections import ChainMap
from collections.abc import AsyncGenerator, Coroutine
from enum import Enum
from typing import Annotated, Literal, Union

from fastapi import APIRouter, HTTPException, Request, WebSocket
from pydantic import BaseModel, Field, RootModel, SecretStr, ValidationError

from .auth import security
from .db import (
    User,
)
from .models import ITorrent, PlexMedia, PlexResponse
from .plex import get_imdb_in_plex, gracefully_get_plex
from .providers import (
    search_for_movie,
    search_for_tv,
)
from .settings import get_settings
from .singleton import get
from .tmdb import ThingType, get_movie_imdb_id, get_tv_imdb_id
from .types import TmdbId
from .utils import Message, non_null

logger = logging.getLogger(__name__)

websocket_ns = APIRouter()


StreamType = Literal['series', 'movie']


class BaseRequest[M, ARGS](BaseModel):
    jsonrpc: Literal['2.0'] = '2.0'
    id: int
    method: M
    args: ARGS
    authorization: SecretStr


class StreamArgs(BaseModel):
    type: StreamType
    tmdb_id: TmdbId
    season: int | None = None
    episode: int | None = None


class StreamRequest(BaseRequest[Literal['stream'], StreamArgs]):
    pass


class PingRequest(BaseRequest[Literal['ping'], None]):
    pass


class PlexArgs(BaseModel):
    tmdb_id: TmdbId
    media_type: ThingType


class PlexRequest(BaseRequest[Literal['plex'], PlexArgs]):
    pass


class Reqs(
    RootModel[
        Annotated[
            Union[StreamRequest, PingRequest, PlexRequest],
            Field(discriminator='method'),
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


class SocketMessageType(str, Enum):
    PONG = 'pong'
    PLEX = 'plex'


class SocketMessage[R](BaseModel):
    jsonrpc: Literal['2.0'] = '2.0'
    id: int
    result: R


class PlexRootResponse(SocketMessage[dict[str, PlexResponse[PlexMedia]]]):
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

    if isinstance(request, StreamRequest):
        args = request.args
        async for item in _stream(
            type=args.type,
            tmdb_id=args.tmdb_id,
            season=args.season,
            episode=args.episode,
        ):
            await websocket.send_json(item.model_dump(mode='json'))

        message = 'Finished streaming'
    elif isinstance(request, PingRequest):
        message = 'Pong'
    elif isinstance(request, PlexRequest):
        message = await plex_method(websocket, request)
    else:
        return await close(websocket, Exception('No such method'))

    if message:
        logger.info(message)
        await websocket.close(reason=message)


async def monitor[T](
    coroutine: Coroutine[None, None, T], name: str, websocket: WebSocket
) -> T:
    start = time.monotonic()
    task = create_task(coroutine, name=name)

    while True:
        if task.done():
            return task.result()
        await sleep(1)
        await websocket.send_json(
            SocketMessage(
                id=-1,
                result={
                    'task_name': task.get_name(),
                    'runtime_seconds': time.monotonic() - start,
                },
            ).model_dump(mode='json')
        )


async def plex_method(
    websocket: WebSocket,
    plex_request: PlexRequest,
) -> None | str:
    args = plex_request.args
    settings = await get(websocket.app, get_settings)

    try:
        plex = await monitor(
            gracefully_get_plex(make_request(websocket, plex_request), settings),
            'gracefully_get_plex',
            websocket,
        )
    except HTTPException as e:
        return await close(websocket, e)

    dat = await get_imdb_in_plex(args.media_type, args.tmdb_id, plex)

    if not dat:
        return await close(websocket, Exception('Not found in plex'))

    await websocket.send_json(
        PlexRootResponse(
            id=plex_request.id,
            data={
                key: PlexResponse[PlexMedia](
                    item=PlexMedia.model_validate(value),
                    server_id=plex.machineIdentifier,
                )
                if value
                else None
                for key, value in dat.items()
            },
        ).model_dump(mode='json')
    )

    return 'Plex complete'
