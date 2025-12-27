release: alembic upgrade head && python seed.py
web: PLEXAPI_PLEXAPI_ENABLE_FAST_CONNECT=1 gunicorn rarbg_local.asgi:app -k uvicorn_worker.UvicornWorker --timeout 90 --keep-alive 5 --log-level debug
