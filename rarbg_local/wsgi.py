import json
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


class CloudflareProxy(object):
    """This middleware sets the proto scheme based on the Cf-Visitor header."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        cf_visitor = environ.get("HTTP_CF_VISITOR")
        if cf_visitor:
            try:
                cf_visitor = json.loads(cf_visitor)
            except ValueError:
                pass
            else:
                proto = cf_visitor.get("scheme")
                if proto is not None:
                    environ['wsgi.url_scheme'] = proto
        return self.app(environ, start_response)


app = create_app(
    {
        'TRANSMISSION_URL': 'http://novell.mause.me:9091/transmission/rpc',
        'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    }
)
app = CloudflareProxy(app)
