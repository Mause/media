import logging
import os

from .new import create_app

logger = logging.getLogger()


if 'SENTRY_DSN' in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        os.environ['SENTRY_DSN'],
        integrations=[SqlalchemyIntegration()],
        release=os.environ['HEROKU_SLUG_COMMIT'],
        traces_sample_rate=1,
    )

app = create_app()

if 'SENTRY_DSN' in os.environ:
    app = SentryAsgiMiddleware(app)
