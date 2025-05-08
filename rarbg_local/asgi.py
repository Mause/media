import logging
import os

from .new import create_app

logger = logging.getLogger(__name__)


if 'SENTRY_DSN' in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    logger.info('Configuring Sentry')

    sentry_sdk.init(
        os.environ['SENTRY_DSN'],
        integrations=[SqlalchemyIntegration()],
        release=os.environ.get('HEROKU_SLUG_COMMIT', os.environ.get('RAILWAY_GIT_COMMIT_SHA')),
        traces_sample_rate=1,
    )
else:
    logger.warn('Not configuring sentry')

app = create_app()

if 'SENTRY_DSN' in os.environ:
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

    app = SentryAsgiMiddleware(app)
