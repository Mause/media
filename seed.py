import asyncio
import os

from fastapi import FastAPI

from rarbg_local.db import (
    Role,
    User,
    create_episode,
    create_movie,
    get_or_create,
    get_session_local,
)
from rarbg_local.singleton import get


async def seed():
    session_maker = await get(FastAPI(), get_session_local)

    with session_maker() as session:
        user = User(
            username='Mause',
            roles=[
                get_or_create(session, Role, name='Admin'),
                get_or_create(session, Role, name='Member'),
            ],
        )
        session.add(user)

        session.add(
            create_movie(
                added_by=user,
                imdb_id='tt0000000',
                tmdb_id=123456,
                title='Programming',
                transmission_id='1',
            )
        )
        session.add(
            create_episode(
                added_by=user,
                title='Coding (Part 1)',
                tmdb_id=123456,
                show_title='Coding',
                episode='1',
                season='1',
                imdb_id='tt0000001',
                transmission_id='2',
            )
        )

        session.commit()


if 'IS_REVIEW_APP' in os.environ or (
    'RAILWAY_ENVIRONMENT_NAME' in os.environ
    and os.environ['RAILWAY_ENVIRONMENT_NAME'].startswith('media-pr-')
):
    print('seeding db')
    asyncio.run(seed())
else:
    print('not seeding db')
