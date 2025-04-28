import os
from asyncio import new_event_loop

from rarbg_local.db import Roles, User, create_episode, create_movie
from rarbg_local.new import get_session_local, get_settings


async def seed():
    settings = await get_settings()
    session_maker = get_session_local(settings)
    with session_maker() as session:
        user = User(
            username='Mause',
            roles=[Roles.Admin, Roles.Member],
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
    new_event_loop().run_until_complete(seed())
else:
    print('not seeding db')
