import logging
import os
from typing import cast

from fastapi import FastAPI

from .config import commit
from .new import create_app

logger = logging.getLogger(__name__)


if sentry_dsn := os.environ.get('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from .sentry.statsig import StatsigIntegration

    logger.info('Configuring Sentry')

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[SqlalchemyIntegration(), StatsigIntegration()],
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
else:
    logger.warning('Not configuring sentry')

app = create_app()

if token := os.environ.get('LOGFIRE_TOKEN'):
    import logfire
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

    logfire.configure(service_name='media-api', service_version=commit, token=token)
    logfire.instrument_fastapi(app, capture_headers=True)
    logfire.instrument_requests()
    logfire.instrument_pydantic()
    logging.getLogger().addHandler(logfire.LogfireLoggingHandler())
    AioHttpClientInstrumentor().instrument()

if sentry_dsn:
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

    app = cast(FastAPI, SentryAsgiMiddleware(app))
