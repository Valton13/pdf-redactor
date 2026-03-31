web: sh web: python start.py
worker: celery -A python.worker.tasks worker --loglevel=info --concurrency=1 --pool=solo
