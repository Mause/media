release: alembic upgrade head && python seed.py
web: gunicorn rarbg_local.wsgi:app --timeout 20 --keep-alive 5 --log-level debug
