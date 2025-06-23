import os

on_heroku = 'HEROKU' in os.environ
production = os.environ.get('RAILWAY_ENVIRONMENT_NAME') == 'production' or on_heroku

commit = os.environ.get('HEROKU_SLUG_COMMIT', os.environ.get('RAILWAY_GIT_COMMIT_SHA'))
