#!/bin/sh

python3 manage.py collectstatic --noinput
python3 create_superuser.py