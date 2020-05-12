release: alembic upgrade head && python seed.py
web: gunicorn rarbg_local.wsgi:app --worker-class gevent --timeout 90 --keep-alive 5 --log-level debug
