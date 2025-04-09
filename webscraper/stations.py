import datetime as dt
import django
import os
from .logging import get_logger

logger = get_logger('__name__')


from .models import Station
from .scraper import WebsiteScraper

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ryazan_ddro.settings')
django.setup()


class StationHttpService:
    """A class to get station data(ids, names, coordinates) from website."""
    def __init__(self, website_scraper_service=WebsiteScraper):
        self.website_scraper_service = website_scraper_service()

    def get_staions_website(self) -> list[dict]:
        weather_reports = self.website_scraper_service.scrape_weather_data()
        stations_data: list[dict] = [
            {
                "ddro_station_id": weather_report["ddro_station_id"],
                "ddro_station_name": weather_report["ddro_station_name"],
                "latitude": float(weather_report["latitude"]),
                "longitude": float(weather_report["longitude"]),
            }
            for weather_report in weather_reports
        ]
        return stations_data


class StationQueryService:
    def __init__(self, station_http_service=StationHttpService):
        self.station_http_service = station_http_service()

    def get_stations_db(self):
        stations_db: list[Station] = [station for station in Station.objects.all()]
        return stations_db

    def update_stations_db(self):
        '''
        Данные станций в базе обновляются перед скрейпингом сайта.
        Идентификатором служит полное наименование станции. Если название
        совпало с базой, но координаты изменились - они обновляются в базе.
        Если же название отсутствует в базе, то новая станция в нее добавляется.
        '''
        stations_db: list[Station] = Station.objects.all()
        stations_website: list[Station] = [
            Station(**data)
            for data
            in self.station_http_service.get_staions_website()
        ]
        stations_db_set: set[str] = set(
            station.ddro_station_name for station in stations_db
        )
        stations_website_set: set[str] = set(
            station.ddro_station_name for station in stations_website
        )
        # Получить совпадающие станции.
        intersection = stations_website_set.intersection(stations_db_set)

        for name in intersection:
            #  Получить объекты станций.
            station_website: Station = next(station for station in stations_website if station.ddro_station_name == name)
            station_db: Station = next(station for station in stations_db if station.ddro_station_name == name)

            # Сравнить объекты и обновить в базе при несовпадении координат обновить в базе.
            if (station_db.latitude != station_website.latitude or station_db.longitude != station_website.longitude):
                # Увеличить счетчик изменения координат для данной станции.
                station_db.position_change_counter += 1
                # Сохранить Время изменения.
                station_db.position_change_time = dt.datetime.now(dt.timezone.utc)
                # Обновить широту и долготу.
                station_db.latitude = station_website.latitude
                station_db.longitude = station_website.longitude
                station_db.save()
            else:
                continue

        # Получить станции, отстуствующие в БД.
        difference: set[str] = stations_website_set.difference(stations_db_set)
        logger.info(
            f'Stations abscent in database: {list(difference)}, '
            f'amount: {len(difference)}'
            )

        # Станции к добавлению в базу.
        stations_difference: list[Station] = [
            station for station
            in stations_website
            if station.ddro_station_name in difference
        ]

        # Добавить новые станции в базу.
        Station.objects.bulk_create(stations_difference)  # IntegrityError, DatabaseError
        logger.info('Updating station database completed.')
