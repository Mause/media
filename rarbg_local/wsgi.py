import os

import sentry_sdk

from .main import create_app

sentry_sdk.init(os.environ['SENTRY_DSN'])
app = create_app(
    {
        'TRANSMISSION_URL': 'http://novell.mause.me:9091/transmission/rpc',
        'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    }
)
