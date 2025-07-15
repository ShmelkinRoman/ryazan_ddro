from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTasks
from eismoinfo_scraper.celery import app
from celery.schedules import crontab


class Command(BaseCommand):
    help = 'Update the Celery Beat schedule dynamically.'

    def add_arguments(self, parser):
        parser.add_argument('task_name', type=str, help='The name of the task to update')
        parser.add_argument('hour', type=int, help='The hour to schedule the task')
        parser.add_argument('minute', type=int, help='The minute to schedule the task')

    def handle(self, *args, **options):
        task_name = options['task_name']
        hour = options['hour']
        minute = options['minute']

        new_crontab = crontab(hour=hour, minute=minute)
        celery_app = app

        if task_name in celery_app.conf.beat_schedule:
            celery_app.conf.beat_schedule[task_name]['schedule'] = new_crontab
            self.stdout.write(self.style.SUCCESS(
                f'Task "{task_name}" updated successfully to run at {hour}:{minute}.'
            ))
            PeriodicTasks.changed()
        else:
            self.stdout.write(self.style.ERROR(
                f'Task "{task_name}" not found in the beat schedule.'
            ))
