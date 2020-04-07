release: alembic upgrade head && python seed.py
web: pyagent run --ssl -- gunicorn rarbg_local.wsgi:app --timeout 90 --keep-alive 5 --log-level debug
