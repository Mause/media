import logging
from collections import ChainMap
from collections.abc import AsyncGenerator
from typing import Annotated, Literal

from fastapi import APIRouter, WebSocket
from fastapi.requests import Request
from pydantic import BaseModel, SecretStr, ValidationError

from .auth import security
from .db import (
    User,
)
from .models import ITorrent
from .providers import (
    search_for_movie,
    search_for_tv,
)
from .singleton import get
from .tmdb import (
    get_movie_imdb_id,
    get_tv_imdb_id,
)
from .types import TmdbId
from .utils import Message, non_null

logger = logging.getLogger(__name__)

websocket_ns = APIRouter()


StreamType = Literal['series', 'movie']


class StreamArgs(BaseModel):
    authorization: SecretStr

    type: StreamType
    tmdb_id: TmdbId
    season: int | None = None
    episode: int | None = None


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


async def authenticate(websocket: WebSocket) -> User:
    def fake(user: Annotated[User, security]) -> User:
        return user

    try:
        user = await get(
            websocket.app,
            fake,
            Request(
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
            ),
        )
    except Exception as e:
        logger.exception('Unable to authenticate websocket request')
        await close(websocket, e)
        raise

    logger.info('Authed user: %s', user)

    return user


async def close(websocket:WebSocket, e: Exception)->None:
    name = type(e).__name__
    message = {'error': str(e), 'type': name}
    if isinstance(e, ValidationError):
        message['errors'] = e.errors()
    await websocket.send_json(message)
    await websocket.close(reason=name)


@websocket_ns.websocket("/ws")
async def websocket_stream(websocket: WebSocket) -> None:
    logger.info('Got websocket connection')
    await websocket.accept()

    try:
        request = StreamArgs.model_validate(await websocket.receive_json())
    except ValidationError as e:
        return await close(websocket, e)

    logger.info('Got request: %s', request)

    user = await authenticate(websocket)

    async for item in _stream(
        type=request.type,
        tmdb_id=request.tmdb_id,
        season=request.season,
        episode=request.episode,
    ):
        await websocket.send_json(item.model_dump(mode='json'))

    logger.info('Finished streaming')
    await websocket.close(reason='Finished streaming')
