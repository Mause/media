import logging
import os
from typing import cast

from fastapi import FastAPI

from .config import commit
from .new import create_app

logger = logging.getLogger(__name__)


if 'SENTRY_DSN' in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    logger.info('Configuring Sentry')

    sentry_sdk.init(
        os.environ['SENTRY_DSN'],
        integrations=[SqlalchemyIntegration()],
        release=commit,
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

if token := os.environ.get('LOGFIRE_TOKEN'):
    import logfire
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

    logfire.configure(
        service_name='media-api', service_version=app.version, token=token
    )
    logfire.instrument_fastapi(app, capture_headers=True)
    logfire.instrument_requests()
    logfire.instrument_sqlalchemy()
    logfire.instrument_pydantic()
    AioHttpClientInstrumentor().instrument()

