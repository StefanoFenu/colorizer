source bin/activate
celery worker -A app.celery --loglevel=info

