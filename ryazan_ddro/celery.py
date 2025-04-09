from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ryazan_ddro.settings')

app = Celery('ryazan_ddro')
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(
    beat_max_loop_interval=1,  # Set to 1 second
    # other configurations...
)


app.conf.beat_schedule = {
    'update_stations': {
        'task': 'webscraper.tasks.update_stations',
        'schedule': crontab(minute=5)
    },
    'save_weather_data': {
        'task': 'webscraper.tasks.save_weather_data',
        'schedule': crontab(minute=10)
    }
}
