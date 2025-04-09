#!/bin/sh

python3 manage.py wait_for_migrations
celery -A ryazan_ddro worker --beat -l info
