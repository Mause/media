import asyncio
import logging
import os
import sys

import backoff
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from sqlalchemy.future import select

from rarbg_local.db import (
    Role,
    User,
    create_episode,
    create_movie,
    get_or_create,
    get_session_local,
)
from rarbg_local.singleton import get

logger = logging.getLogger(__name__)
logging.getLogger('backoff').addHandler(logging.StreamHandler())


async def seed():
    session_maker = await get(FastAPI(), get_session_local)

    with session_maker() as session:
        first = (
            session.execute(select(User).filter_by(username='Mause')).scalars().first
        )

        user = backoff.on_exception(
            backoff.expo,
            OperationalError,
            max_time=60,
        )(first)()

        if not user:
            user = User(
                username='Mause',
                email='me@mause.me',
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
                episode=1,
                season=1,
                imdb_id='tt0000001',
                transmission_id='2',
            )
        )

        session.commit()


do_seed = (
    'IS_REVIEW_APP' in os.environ
    or (
        'RAILWAY_ENVIRONMENT_NAME' in os.environ
        and os.environ['RAILWAY_ENVIRONMENT_NAME'].startswith('media-pr-')
    )
    or '--force' in sys.argv
)
if do_seed:
    logger.info('seeding db')
    asyncio.run(seed())
else:
    logger.info('not seeding db')
