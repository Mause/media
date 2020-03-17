release: alembic upgrade head && python seed.py
web: pyagent run -- gunicorn rarbg_local.wsgi:app --timeout 20 --keep-alive 5 --log-level debug
