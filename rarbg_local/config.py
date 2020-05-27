import json
import os
from base64 import b64decode
from urllib.parse import urlparse

from walter.config import Config, ConfigErrors


def validate_jwt(string):
    assert string.count('.') == 2
    header, body, sig = string.split('.')
    json.loads(b64decode(header))
    json.loads(b64decode(body))


in_prod = 'HEROKU' in os.environ


class DConfig(Config):
    def __call__(
        self,
        name,
        required=True,
        validate=lambda value: None,
        cast=lambda a: a,
        **kwargs
    ):
        if not required:
            kwargs.setdefault('default', None)

        def _cast(value):
            validate(value)
            return cast(value)

        return super().__call__(name, cast=_cast, **kwargs)


config = DConfig('Elliana May', 'Media')

CLOUDAMQP_URL = config('CLOUDAMQP_URL', validate=urlparse)
DATABASE_URL = config('DATABASE_URL', validate=urlparse)
PLEX_USERNAME = config('PLEX_USERNAME')
PLEX_PASSWORD = config('PLEX_PASSWORD')

TIMBERIO_APIKEY = config('TIMBERIO_APIKEY', required=in_prod, validate=validate_jwt)
TIMBERIO_SOURCEID = config('TIMBERIO_SOURCEID', validate=int, required=in_prod)
HEROKU_SLUG_COMMIT = config('HEROKU_SLUG_COMMIT', required=in_prod)
SENTRY_DSN = config('SENTRY_DSN', required=in_prod)


def check_config():
    if config.errors:
        raise ConfigErrors(errors=config.errors)
