# create_superuser.py
import os
import django
import environ
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

env = environ.Env()

username = env('USERNAME')
email = env('EMAIL')
password = env('PASSWORD')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ryazan_ddro.settings')
django.setup()

User = get_user_model()


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating superuser...')
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            print(f"Superuser '{username}' created.")
        else:
            print(f"Superuser '{username}' already exists.")
