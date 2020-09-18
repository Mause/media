# import eventlet
#  --worker-class eventlet -w 1
#
# eventlet.monkey_patch()
import json
import logging
import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .logger import get_timber_handler
from .main import create_app

logger = logging.getLogger()


if 'TIMBERIO_APIKEY' in os.environ:
    logger.addHandler(get_timber_handler())


if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(
        os.environ['SENTRY_DSN'],
        integrations=[FlaskIntegration(), SqlalchemyIntegration()],
        release=os.environ['HEROKU_SLUG_COMMIT'],
        traces_sample_rate=0.75,
    )


class CloudflareProxy:
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


_app = create_app(
    {
        'TRANSMISSION_URL': 'http://novell.mause.me:9091/transmission/rpc',
        'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    }
)
app = CloudflareProxy(_app)
