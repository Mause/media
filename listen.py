import asyncio
from asyncio import create_task

import uvloop
from psycopg import AsyncConnection, connect


async def listener(conn: AsyncConnection) -> None:
    await conn.execute("LISTEN my_channel")
    async for msg in conn.notifies():
        print(f"Received notification: {msg.payload}")  # noqa: T201


async def publisher(conn: AsyncConnection) -> None:
    while True:
        await conn.execute("NOTIFY my_channel, 'Hello, world!'")
        await asyncio.sleep(5)
        print('pub')  # noqa: T201


async def main() -> None:
    import pudb

    pudb.set_trace()
    conn = await AsyncConnection.connect("dbname=postgres")
    create_task(publisher(conn))
    await listener(conn)


if __name__ == "__main__":
    # psycopg.init()
    # psycopg.set_wait_callback(psycopg.ASYNC_IO_WAIT_CALLBACK)
    uvloop.run(main())
