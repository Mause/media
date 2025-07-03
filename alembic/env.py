import logging
import os
import sqlite3
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Any, cast

import backoff
import sqlalchemy.pool.base
from sqlalchemy import (
    engine_from_config,
    event,
    pool,
)
from sqlalchemy.exc import OperationalError

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

bolog = logging.getLogger('backoff')
bolog.setLevel(logging.INFO)
bolog.addHandler(logging.StreamHandler())


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
db = __import__('rarbg_local.db').db

if 'HEROKU' in os.environ or 'RAILWAY_SERVICE_ID' in os.environ:
    url = (
        os.environ['DATABASE_URL']
        .replace('postgres://', 'postgresql+psycopg://')
        .replace('postgresql://', 'postgresql+psycopg://')
    )
else:
    url = 'sqlite:///' + str(Path(__file__).parent.parent.absolute() / 'db.db')


alembic_config = cast(dict[str, Any], config.get_section(config.config_ini_section, {}))
assert alembic_config

# we only override if it's not already set
alembic_config.setdefault('sqlalchemy.url', url)
target_metadata = db.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        dialect_name='postgresql',
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = engine_from_config(
        alembic_config,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
        pool_pre_ping=True,
        connect_args={
            'connect_timeout': 10000,
        }
        if 'postgres' in url
        else {},
    )
    sqlite = connectable.url.get_backend_name() == 'sqlite'
    if sqlite:

        @event.listens_for(connectable, 'connect')
        def _fk_pragma_on_connect(
            dbapi_con: sqlite3.Connection,
            con_record: sqlalchemy.pool.base._ConnectionRecord,
        ) -> None:
            dbapi_con.create_collation(
                "en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1
            )
            dbapi_con.execute('pragma foreign_keys=ON')

        retrying_connect = backoff.on_exception(
            backoff.expo, OperationalError, max_time=60
        )(connectable.connect)
    else:
        retrying_connect = connectable.connect

    with retrying_connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
