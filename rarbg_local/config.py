import json
from base64 import b64decode
from urllib.parse import urlparse
from uuid import UUID

from walter.config import Config


def load_jwt(string):
    assert string.count('.') == 2
    header, body, sig = string.split('.')
    json.loads(b64decode(header))
    json.loads(b64decode(body))
    return string


with Config('Elliana May', 'Media') as config:
    CLOUDAMQP_APIKEY = config('CLOUDAMQP_APIKEY', cast=UUID)
    CLOUDAMQP_URL = config('CLOUDAMQP_URL', cast=urlparse)
    DATABASE_URL = config('DATABASE_URL', cast=urlparse)
    PLEX_USERNAME = config('PLEX_USERNAME')
    PLEX_PASSWORD = config('PLEX_PASSWORD')

    TIMBERIO_APIKEY = config('TIMBERIO_APIKEY', cast=load_jwt)
    TIMBERIO_SOURCEID = config('TIMBERIO_SOURCEID', cast=int)
    HEROKU_SLUG_COMMIT = config('HEROKU_SLUG_COMMIT')
    SENTRY_DSN = config('SENTRY_DSN', default=None)
