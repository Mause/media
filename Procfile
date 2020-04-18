release: alembic upgrade head && python seed.py
web: gunicorn --worker-class eventlet -w 1 rarbg_local.wsgi:app --timeout 90 --keep-alive 5 --log-level debug
