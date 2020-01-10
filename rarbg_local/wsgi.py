import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .main import create_app

sentry_sdk.init(
    os.environ['SENTRY_DSN'],
    integrations=[FlaskIntegration(), SqlalchemyIntegration()],
    release=os.environ['HEROKU_SLUG_COMMIT'],
)
app = create_app(
    {
        'TRANSMISSION_URL': 'http://novell.mause.me:9091/transmission/rpc',
        'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    }
)
