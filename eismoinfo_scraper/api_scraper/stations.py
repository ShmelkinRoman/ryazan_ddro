import math
import asyncio
import datetime as dt


from .requests import WeatherDataHttpClient, StationDataHttpClient
from .loggers import get_logger
from .models import Station

# Логгирование.
logger = get_logger(__name__)


class StationException(Exception):
    def __init__(self, message):
        super().__init__(message)


class StationHttpService:
    """A class to get station data(ids, coordinates) from API."""
    def __init__(
            self, 
            weatherdata_http_client=WeatherDataHttpClient(),
            stationdata_http_client=StationDataHttpClient()):
        self.weatherdata_http_client = weatherdata_http_client
        self.stationdata_http_client = stationdata_http_client

    def get_stations_current_weather(self) -> list[dict]:
        """
        Return each station's id, coordinates and location name(in a dict)
        from the current weather report.
        """
        resp_array = asyncio.run(self.weatherdata_http_client.get_current_weather())
        # resp_array = resp.json()  # JSONDecodeError
        if resp_array == []:
            logger.error('Current weather reports: empty report array!')
        stations_current_weather: list[dict] = [
            {
                'eismo_station_id': int(report['id']),  # KeyError, ValueError, TypeError
                'latitude': float(report['lat']),
                'longitude': float(report['lng']),
                'city_name': str(report['irenginys']),
                'road_name': str(report['pavadinimas']),
                'road_number': str(report['numeris'])
            }
            for report in resp_array
        ]
        logger.info('List of stations from current weather report obtained.')
        return stations_current_weather

    def get_station_height(
            self, station_id: int,
            latitude: float, longitude: float) -> float | None:
        resp = asyncio.run(self.stationdata_http_client.fetch_station_height(
            station_id=station_id,
            latitude=latitude,
            longitude=longitude
            )
        )
        return resp


class StationQueryService:
    """Класс для работы с данными станций в БД."""

    def __init__(self, station_http_service=StationHttpService):
        self.station_http_service = station_http_service()

    def get_stations_from_db(self) -> list[Station]:
        """
        Вернуть массив из всех объектов станций, существующих в БД.
        """
        stations_db = [station for station in Station.objects.all()]
        logger.info('List of stations from the database obtained.')
        return stations_db

    def update_heights(self):
        logger.info('Updating station heights started.')
        stations = self.get_stations_from_db()
        for station in stations:
            station.height = self.station_http_service.get_station_height(
                station_id=station.eismo_station_id,
                latitude=station.latitude,
                longitude=station.longitude
            )
            station.save()
        logger.info('Updating station heights completed.')

    def update_stations_db(self):
        """
        Обновить список станций БД, обновить координаты всех станции.
        """
        # Получить станции из БД.
        stations_db: list[Station] = self.get_stations_from_db()

        # Получить список станций из текущего отчета погоды.
        stations_current: list[Station] = [
            Station(**data)
            for data
            in self.station_http_service.get_stations_current_weather()
        ]

        # Сделать множества eismo_station_id(только уникальные значения)
        # из полученных списков станций.
        stations_db_set: set[int] = set(
            station.eismo_station_id for station in stations_db
        )
        stations_current_set: set[int] = set(
            station.eismo_station_id for station in stations_current
        )

        # Для тех станций, которые есть и в базе и в текущем отчете,
        # обновить координаты в базе при несовпадении.
        intersection = stations_current_set.intersection(stations_db_set)
        for id in intersection:
            #  Получить объекты станций.
            station_current = [
                station for station in stations_current if station.eismo_station_id == id
                ][0]  # поменять на next()
            station_db = [
                station for station in stations_db if station.eismo_station_id == id
                ][0]

            # Если координаты станции из текущего отчета погоды не совпадают
            # с координатами в базе, то обновляем их.
            if (station_db.latitude != station_current.latitude or station_db.longitude != station_current.longitude):
                # Увеличить счетчик изменения координат для данной станции.
                station_db.position_change_counter += 1
                # Сохранить Время изменения.
                station_db.position_change_time = dt.datetime.now(dt.timezone.utc)

                # Обновить широту и долготу.
                station_db.latitude = station_current.latitude
                station_db.longitude = station_current.longitude

                # Обновить название города и дороги.
                station_db.city_name = station_current.city_name
                station_db.road_name = station_current.road_name
                station_db.road_number = station_current.road_number
                station_db.save()

        # Получить станции, отстуствующие в БД.
        difference: set[int] = stations_current_set.difference(stations_db_set)
        logger.info(
            f'Stations abscent in database: {list(difference)}, '
            f'amount: {len(difference)}'
            )
        # Станции к добавлению в базу.
        stations_difference: list[Station] = [
            station for station
            in stations_current
            if station.eismo_station_id in difference
        ]
        # Присвоить станциям высоту.
        stations_to_add = []
        for station in stations_difference:
            stations_to_add.append(station)
        # Создать новые объекты станций в базе.
        Station.objects.bulk_create(stations_to_add)  # IntegrityError, DatabaseError
        logger.info('Updating station database completed.')
