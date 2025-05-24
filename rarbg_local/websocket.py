import logging
from collections import ChainMap
from typing import Annotated, Literal

from fastapi import APIRouter, WebSocket
from fastapi.requests import Request
from pydantic import BaseModel, SecretStr, ValidationError

from .auth import security
from .db import (
    User,
)
from .providers import (
    search_for_movie,
    search_for_tv,
)
from .singleton import get
from .tmdb import (
    get_movie_imdb_id,
    get_tv_imdb_id,
)
from .utils import Message, TmdbId, non_null

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
    type: str,
    tmdb_id: TmdbId,
    season: int | None = None,
    episode: int | None = None,
):
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
            yield item.model_dump(mode='json')


@websocket_ns.websocket("/ws")
async def websocket_stream(websocket: WebSocket):
    def fake(user: Annotated[User, security]):
        return user

    logger.info('Got websocket connection')
    await websocket.accept()

    try:
        request = StreamArgs.model_validate(await websocket.receive_json())
    except ValidationError as e:
        await websocket.send_json(
            {'error': str(e), 'type': type(e).__name__, 'errors': e.errors()}
        )
        await websocket.close(reason=type(e).__name__)
        return
    logger.info('Got request: %s', request)

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
        await websocket.send_json({'error': str(e), 'type': type(e).__name__})
        await websocket.close(reason=type(e).__name__)
        raise

    logger.info('Authed user: %s', user)

    async for item in _stream(
        type=request.type,
        tmdb_id=request.tmdb_id,
        season=request.season,
        episode=request.episode,
    ):
        await websocket.send_json(item)

    logger.info('Finished streaming')
    await websocket.close(reason='Finished streaming')
