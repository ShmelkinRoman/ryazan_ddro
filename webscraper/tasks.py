from celery import shared_task

from .stations import StationQueryService
from .weatherdata_service import WeatherDataService


@shared_task
def update_stations():
    service = StationQueryService()
    service.update_stations_db()


@shared_task
def save_weather_data():
    service = WeatherDataService()
    service.save_current_weather()
