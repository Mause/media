import logging
import os
from typing import cast

from fastapi import FastAPI

from pythonjsonlogger.json import JsonFormatter

from .new import create_app

logger = logging.getLogger(__name__)

if 'RAILWAY_ENVIRONMENT_NAME' in os.environ:
    logger.info("We're running on Railway!")
    root_logger = logging.getLogger()
    log_handler = logging.StreamHandler()
    formatter = JsonFormatter("%(message)s%(asctime)s%(exc_info)s%(levelname)s")
    log_handler.setFormatter(formatter)
    root_logger.addHandler(log_handler)
elif 'HEROKU' in os.environ:
    logger.info("We're running on Heroku!")
else:
    logger.info("We're not running on a cloud platform")

if 'SENTRY_DSN' in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    logger.info('Configuring Sentry')

    sentry_sdk.init(
        os.environ['SENTRY_DSN'],
        integrations=[SqlalchemyIntegration()],
        release=os.environ.get(
            'HEROKU_SLUG_COMMIT', os.environ.get('RAILWAY_GIT_COMMIT_SHA')
        ),
        # Add data like request headers and IP for users, if applicable;
        send_default_pii=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1,
        # To collect profiles for all profile sessions,
        # set `profile_session_sample_rate` to 1.0.
        profile_session_sample_rate=1.0,
        # Profiles will be automatically collected while
        # there is an active span.
        profile_lifecycle="trace",
    )

    app = cast(FastAPI, SentryAsgiMiddleware(create_app()))
else:
    logger.warning('Not configuring sentry')
    app = create_app()
