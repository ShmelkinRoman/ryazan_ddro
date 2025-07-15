# create_superuser.py
import os
import django
import environ
from django.contrib.auth import get_user_model

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eismoinfo_scraper.settings')
django.setup()

env = environ.Env()

User = get_user_model()


def create_superuser(username, email, password):

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username, email=email, password=password
        )
        print(f"Superuser '{username}' created.")
    else:
        print(f"Superuser '{username}' already exists.")


if __name__ == '__main__':
    username = env('USERNAME')
    email = env('EMAIL')
    password = env('PASSWORD')
    create_superuser(
        username=username,
        email=email,
        password=password
    )
