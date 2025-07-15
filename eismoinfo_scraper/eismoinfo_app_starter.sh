#!/bin/sh

python3 manage.py wait_for_db
python3 manage.py makemigrations
python3 manage.py makemigrations api_scraper
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 /code/create_superuser.py

python3 manage.py loaddata api_scraper/data/wind_degree.json
python3 manage.py loaddata api_scraper/data/surface_condition.json
python3 manage.py loaddata api_scraper/data/precipitation_type.json

gunicorn -w 2 -b 0:8000 eismoinfo_scraper.wsgi:application
# python3 manage.py runserver 0.0.0.0:8000