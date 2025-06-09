import asyncio

from pytest import mark

from ..utils import Message, create_monitored_task


async def coro(queue: asyncio.Queue[int | Message]):
    await queue.put(1)


@mark.asyncio
async def test_create_monitored_task():
    output_queue = asyncio.Queue[int | Message]()

    create_monitored_task(coro(output_queue), output_queue.put_nowait)

    assert await output_queue.get() == 1
    message = await output_queue.get()
    assert isinstance(message, Message)
    assert message.event == 'exit'
