#!/bin/sh

python3 manage.py wait_for_db
python3 manage.py collectstatic --noinput
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py wait_for_migrations
python3 manage.py create_superuser

gunicorn -w 2 -b 0:8000 ryazan_ddro.wsgi:application
