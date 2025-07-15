import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError


class Command(BaseCommand):
    help = 'Wait for the database to be available and for migrations to be applied'

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        print('WAIT FOR DB LAUNCHED')

        # Wait for the database to be available
        while not db_conn:
            try:
                db_conn = connections['default']
                db_conn.cursor()
            except OperationalError:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))

        # Now wait for migrations to be applied
        self.stdout.write('Waiting for migrations to be applied...')
        migration_complete = False

        while not migration_complete:
            try:
                with db_conn.cursor() as cursor:
                    # Replace 'your_table_name' with an actual table name that should exist after migrations
                    cursor.execute("SELECT 1 FROM django_celery_beat_periodictask LIMIT 1;")
                    migration_complete = True
            except (OperationalError, ProgrammingError):
                self.stdout.write('Migrations not yet applied, waiting 3 seconds...')
                time.sleep(3)

        self.stdout.write(self.style.SUCCESS('Migrations have been applied!'))
