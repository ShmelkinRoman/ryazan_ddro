#!/bin/sh
python3 manage.py wait_for_db
python3 manage.py wait_for_migrations
celery -A eismoinfo_scraper worker --beat -l info
