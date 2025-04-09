import django
import os
from django.db import IntegrityError as IntegrityError_1
from django.db.utils import IntegrityError as IntegrityError_2


from .scraper import WebsiteScraper
from .parsing import WeatherDictParser
from .stations import StationQueryService
from .models import WeatherData, Station
from .logging import get_logger

# Логгирование.
logger = get_logger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ryazan_ddro.settings')
django.setup()


class WeatherDataService:
    def __init__(
            self, website_scraper_service=WebsiteScraper,
            parsing_service=WeatherDictParser,
            station_query_service=StationQueryService
    ):
        self.website_scraper_sevice = website_scraper_service()
        self.parsing_service = parsing_service()
        self.station_query_service = station_query_service()

    def save_weather_data(
        self,
        parsed_reports_with_stat_pks: list[dict]
    ) -> bool:
        for report in parsed_reports_with_stat_pks:
            object = WeatherData(**report)
            try:
                object.save()
                logger.info(
                    f'Station pk={report["station"]} '
                    f'weather data saved.')
            except (IntegrityError_1, IntegrityError_2):
                logger.warning(
                    f'Station pk={report["station"]} '
                    f'station_localtime_unique_constraint has been violated.'
                )

    def indentify_stations(self, parsed_reports: list[dict]) -> list[dict]:
        stations_db: list[Station] = self.station_query_service.get_stations_db()
        parsed_reports_with_stat_pks: list[dict] = []
        for report in parsed_reports:
            name = report['ddro_station_name']
            match: Station = next((station for station in stations_db if station.ddro_station_name == name), None)
            if match:
                report['station'] = match
                del report['ddro_station_id']
                del report['ddro_station_name']
                del report['latitude']
                del report['longitude']
                parsed_reports_with_stat_pks.append(report)
            else:
                logger.warning(f'Station {name} '
                               f'was not identified in database.')
                continue
        # print('parsed_reports_with_stat_pks count =', len(parsed_reports_with_stat_pks))
        # print('parsed_reports_with_stat_pks', parsed_reports_with_stat_pks)
        return parsed_reports_with_stat_pks

    def save_current_weather(self):
        # Под некоторыми ключами словаря может оказаться None при ошибке при скрепинге сайта.
        weather_reports_arr: list[dict] = self.website_scraper_sevice.scrape_weather_data()
        # print('WEATHER REPORT_ARR count', len(weather_reports_arr))
        # print('WEATHER REPORT_ARR =', weather_reports_arr)

        # ValueError может быть при парсинге значений, например попала temperature_air = 'abc'.
        parsed_reports: list[dict] = self.parsing_service.get_parsed_weather_reports(weather_reports_arr=weather_reports_arr)

        # 1. Станции в базе обновляются перед скрейпингом погодных данных.
        # Но если в погодные отчеты попала неизвестная базе станция,
        # то ее отчеты не попадают в базу.

        # 2. IntegrityError может быть при попытке нарушении правила:
        # "В базе может быть только один отчет от определенной стации за опред момент времени."
        parsed_reports_with_stat_pks = self.indentify_stations(parsed_reports=parsed_reports)
        self.save_weather_data(parsed_reports_with_stat_pks)
