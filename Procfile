release: alembic upgrade head && python scripts/seed.py
web: gunicorn rarbg_local.asgi:app -k uvicorn.workers.UvicornWorker --timeout 90 --keep-alive 5 --log-level debug
