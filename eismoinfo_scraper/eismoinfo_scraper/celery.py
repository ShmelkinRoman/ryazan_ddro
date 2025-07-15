from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eismoinfo_scraper.settings')

app = Celery('eismoinfo_scraper')
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
        'task': 'api_scraper.tasks.update_stations',
        'schedule': crontab(hour=14, minute=30)
    },
    'update_heights': {
        'task': 'api_scraper.tasks.update_station_heights',
        'schedule': crontab(hour=14, minute=30)
    },
    'save_data_last_day': {
        'task': 'api_scraper.tasks.save_weather_data_last_day',
        'schedule': crontab(minute=10)
    },
    'save_data_last_hour': {
        'task': 'api_scraper.tasks.save_weather_data_last_hour',
        'schedule': crontab(minute=0),
    },
    'save_current_data': {
        'task': 'api_scraper.tasks.save_current_weather_data',
        'schedule': crontab(minute=0),
    }
}
