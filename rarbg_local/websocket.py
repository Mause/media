import logging
from collections import ChainMap
from collections.abc import AsyncGenerator
from typing import Annotated, Literal

from fastapi import APIRouter, WebSocket
from fastapi.requests import Request
from fastapi.responses import JSONResponse
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
        await websocket.send_json(item.model_dump(mode='json'))

    logger.info('Finished streaming')
    await websocket.close(reason='Finished streaming')


def get_asyncapi():
    return {
        "asyncapi": '3.0.0',
        'info': {
            'title': 'Create an AsyncAPI document for an API with WebSocket',
            'version': '1.0.0',
        },
        'servers': {
            'production': {
                'host': "media.mause.me",
                'pathname': "/ws",
                'protocol': "wss",
            }
        },
        'operations': {
            'helloListener': {
                'action': 'receive',
                'channel': {'$ref': '#/channels/root'},
                'messages': [
                    {'$ref': '#/channels/root/messages/get_messages'},
                    {'$ref': '#/channels/root/messages/results'},
                ]
            },
        },
        'channels': {
            'root': {
                'address': '/',
                'messages': {
                    'get_results': {
                        'payload': {'$ref': '#/components/schemas/StreamArgs'}
                    },
                    'results': {
                        'payload': {'$ref': '#/components/schemas/ITorrent'}
                    }
                },
                'bindings': {
                    'ws': {
                        'query': {
                            'type': 'object',
                            'properties': {}
                        }
                    }
                }
            }
        },
        'components': {
            'messages': {},
            'schemas': {
                'StreamArgs': StreamArgs.model_schema(),
                'ITorrent': ITorrent.model_schema(),
            }
        }
    }


@websocket_ns.get('/asyncapi.json')
async def asyncapi_json():
    return JSONResponse(get_asyncapi())
