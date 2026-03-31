web: sh -c 'uvicorn python.api.main:app --host 0.0.0.0 --port ${PORT:-8000}'
worker: celery -A python.worker.tasks worker --loglevel=info --concurrency=1 --pool=solo
