from celery import shared_task

from .stations import StationQueryService
from .weather_data_service import WeatherDataService
from .loggers import get_logger


logger = get_logger(__name__)


@shared_task
def update_stations():
    station_service = StationQueryService()
    try:
        station_service.update_stations_db()
    except Exception as e:
        logger.error(e, exc_info=True)  # Что это?


@shared_task
def update_station_heights():
    station_service = StationQueryService()
    station_service.update_heights()


@shared_task
def save_current_weather_data():
    weather_data_service = WeatherDataService(mode='current')
    # Расследование...
    wind_degree_queryset = weather_data_service.parsing_service.parsing_models_dict['wind_degree'].queryset
    for e in wind_degree_queryset:
        logger.info('PRINTING WIND DEGREE QUERYSET')
        logger.info(f'code = {e.code}', f'value_api = {e.value_api}')
    weather_data_service.save_current_weather()
    logger.info('Current weather saved successfully.')


@shared_task
def save_weather_data_last_hour():
    weather_data_service = WeatherDataService(mode='retrospective')

    # Расследование...
    wind_degree_queryset = weather_data_service.parsing_service.parsing_models_dict['wind_degree'].queryset
    for e in wind_degree_queryset:
        logger.info('PRINTING WIND DEGREE QUERYSET')
        logger.info(f'code = {e.code}', f'value_api = {e.value_api}')

    weather_data_service.save_retrospective_weather(period='last_hour')
    logger.info('Saving weather data last hour completed.')


@shared_task
def save_weather_data_last_day():
    weather_data_service = WeatherDataService(mode='retrospective')
    weather_data_service.save_retrospective_weather(period='last_day')
    logger.info('Saving weather data last day completed.')
