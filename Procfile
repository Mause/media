release: alembic upgrade head && python seed.py
web: gunicorn rarbg_local.asgi:app -k uvicorn_worker.UvicornWorker --timeout 90 --keep-alive 5 --log-level debug
