import asyncio
import datetime as dt

from rest_framework.exceptions import ValidationError
from json.decoder import JSONDecodeError
from requests import Response
from zoneinfo import ZoneInfo

from .serializers import ApiScraperWeatherDataSerializer
from .requests import WeatherDataHttpClient
from .stations import StationQueryService
from .parsing import WeatherDictParser
from .models import Station, StationRequestResult
from .station_request_result import StationRequestResultQueryService
from .loggers import get_logger


logger = get_logger(__name__)


class WeatherDataException(Exception):
    """Кастомный класс исключения для погодных данных."""
    def __init__(self, error: str, message=None):
        self.error = error
        self.message = message


class WeatherDataService:
    """Класс для получения, преобразования и сохраниения погодных данных."""

    TIMEZONE_API = 'Europe/Vilnius'

    def __init__(
        self,
        mode: str,
        weatherdata_http_client=WeatherDataHttpClient(),
        station_query_service=StationQueryService(),
        parsing_service=WeatherDictParser,
        station_result_query_service=StationRequestResultQueryService(),
    ):
        self.weatherdata_http_client = weatherdata_http_client
        self.station_query_service = station_query_service
        if mode == 'retrospective':
            self.parsing_service = parsing_service(mode='retrospective')
        elif mode == 'current':
            self.parsing_service = parsing_service(mode='current')
        elif mode == 'current_weather_parsing':
            self.parsing_service = parsing_service(mode='current_weather_parsing')

        self.station_result_query_service = station_result_query_service

    def fetch_current_weather(self):
        """
        Вернуть текущие показания станций в формате БД.
        """
        # Обновить список станций в БД.
        self.station_query_service.update_stations_db()

        # Вернуть массив словарей Python(декодированную json строку).
        resp = asyncio.run(self.weatherdata_http_client.get_current_weather())

        # Преобразовать в формат БД.
        parsed_reports: list[dict] = self.parsing_service.get_parsed_weather_reports(
            eismo_reports=resp
        )
        return parsed_reports

    def save_current_weather(self):
        parsed_reports: list[dict] = self.fetch_current_weather()
        self.save_weather_data(parsed_reports=parsed_reports)

    def save_retrospective_weather(self, period: str):
        """
        Получить, перобразовать в формат БД и сохранить погодные данные
        от каждой станций из БД за прошедший час или сутки по Литве.
        """
        # Обновить список станций в БД.
        self.station_query_service.update_stations_db()

        stations = self.get_stations()
        match period:
            case 'last_hour':
                number_of_reports = 50
            case 'last_day':
                number_of_reports = 1000

        # Опрос каждой станции.
        for station in stations:
            try:
                status = StationRequestResult.Status.SUCCESS
                error_message = None
                earliest_report_time, latest_report_time, reports_count = (
                    None, None, None
                )
                # Получить ответ от станции JSON -> list[dict]
                resp = self.get_station_reports(
                    station=station, number_of_reports=number_of_reports
                    )

                # Отфильтровать отчеты за указанный период времени.
                timely_filtered_reports = self.get_timely_filtered_reports(
                    period=period,
                    resp=resp
                )

                # Преобразовать данные в отчетах в формат БД.
                parsed_reports = self.parsing_service.get_parsed_weather_reports(
                    station=station,
                    eismo_reports=timely_filtered_reports
                )

                #  Если станция в списке станций, от которых получены неизвестные парсинговым моделям значения.
                if station.eismo_station_id in self.parsing_service.stations_to_refetch:
                    raise WeatherDataException(
                        error='unknown_parsing_values'
                    )

                # Сохранить преобразованные погодные отчеты в БД.
                self.save_weather_data(
                    parsed_reports=parsed_reports
                )
                logger.info(
                    f'Station {station.eismo_station_id}: reports saved to db amount: '
                    f'{len(parsed_reports)}.'
                )
                earliest_report_time, latest_report_time, reports_count = self.get_earl_latest_reptime(parsed_reports)

            # requests.py
            except JSONDecodeError as de:
                logger.error(f'Station {station}: JSON decode error.')
                status = StationRequestResult.Status.JSON_DECODE_ERROR,
                error_message = de.message

            # parsing.py: отсутствует ожидаемый ключ в ответе станции,
            # ошибка при преобразовании данных.
            except (KeyError, TypeError, ValueError) as err:
                logger.error(f'Station {station}: parsing error.')
                status = StationRequestResult.Status.PARSING_ERROR
                error_message = err

            # Методы self.get_station_reports()
            # и self.get_timely_filtered_reports()
            except WeatherDataException as e:
                logger.error(
                    f'Station {station.eismo_station_id}: {e.error}: message: {e.message}.'
                )
                error = e.error
                error_message = e.message
                match error:
                    # Превышено количество попыток получить ответ.
                    # (или ни разу не получен 200)
                    case 'http_request_error':
                        status = StationRequestResult.Status.HTTP_REQUEST_ERROR

                    # Пустой массив в ответе от станции.
                    case 'empty_report_array':
                        status = StationRequestResult.Status.EMPTY_REPORT_ERROR

                    # Ни один из погодных отчетов станции не попал
                    # в диапазон предыдущих суток по Литве.
                    case 'out_of_timerange':
                        status = StationRequestResult.Status.OUT_OF_TIMERANGE_ERROR

                    # Получены значения, отстуствующие с парсинговых моделях.
                    case 'unknown_parsing_values':
                        status = StationRequestResult.Status.UNKNOWN_PARSING_VALUES_ERROR

            # serializers.py, наиболее вероятно по
            # причине нарушения UniqueConstraint полей station и unix,
            # поскольку на данном этапе сами погодные данные уже
            # преобразованы в нужные типы данных без ошибок.
            except ValidationError as e:
                logger.error(
                    f'Station {station.eismo_station_id}: '
                    f'validation error: station_unix_unique_constraint failed.'
                    )
                status = StationRequestResult.Status.VALIDATION_ERROR
                error_message = str(e.detail)[:200]

            finally:
                # Сохранить отчет по результатам запроса.
                StationRequestResult.objects.create(
                    station=station,
                    status=status,
                    error_message=error_message,
                    earliest_report_time=earliest_report_time,
                    latest_report_time=latest_report_time,
                    reports_count=reports_count
                )

        logger.info(
            'Stations to request again(respose contains unknown parsing values): '
            f'{self.parsing_service.stations_to_refetch}.'
        )
        # Добавить новые литовские значения в базу.
        self.parsing_service.update_parsing_models()

    def get_stations(self) -> list[Station]:
        """Получить все станции из БД."""
        stations = self.station_query_service.get_stations_from_db()
        stations.sort(key=lambda x: x.eismo_station_id)
        return stations

    def get_stations_to_refetch(self) -> list[Station]:
        """
        Получить список станций,
        при опросе которых сегодня возникла ошибка.
        """
        utc_now = dt.datetime.now(dt.timezone.utc)
        utc_today_start = dt.datetime.combine(utc_now, dt.time())
        utc_today_end = dt.datetime.combine(utc_now, dt.time(23, 59))
        stations = [
            request_result.station
            for request_result
            in self.station_result_query_service.get_request_results(
                request_status='ERROR',
                start=utc_today_start,
                end=utc_today_end
            )
        ]
        print(stations)
        return stations

    def get_station_reports(
        self,
        station: Station,
        number_of_reports: int
    ) -> Response | None:
        """
        Получить архивные погодные данные от указанной станции
        на заданное количество отчетов с момента выполнения запроса.
        """
        # Выполнить запрос к стации в синхронном режиме.
        resp = asyncio.run(self.weatherdata_http_client.get_retrospective_weather(
            station_id=station.eismo_station_id,
            number_of_reports=number_of_reports
            )
        )
        if resp == []:
            raise WeatherDataException(error='empty_report_array')
        elif resp is None:
            raise WeatherDataException(
                error='http_request_error',
                message='max retries exceeded'
                )
        return resp

    def get_timely_filtered_reports(
        self,
        resp: list[dict],
        period: str
    ) -> list[dict] | None:
        """
        Отфильтровать отчеты за указанный период.
        """
        # Текущее время в UTC.
        utc_now = dt.datetime.now(dt.timezone.utc)

        # Текущее время по Литве в datetime.
        lithuanian_timezone = ZoneInfo(self.TIMEZONE_API)
        lithuanian_now = utc_now.astimezone(lithuanian_timezone)
        if period == 'last_hour':
            # Начало предыдущего часа по Литве.
            start = lithuanian_now.replace(
                minute=0, second=0, microsecond=0) - dt.timedelta(hours=1)

            # Начало текущего часа по Литве.
            end = lithuanian_now.replace(
                minute=0, second=0, microsecond=0)

        elif period == 'last_day':
            # 00:00 вчера по Литве.
            start = lithuanian_now.replace(hour=0, minute=0, second=0, microsecond=0) - dt.timedelta(days=1)

            # 00:00 сегодня по Литве.
            end = lithuanian_now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Отфильтровать отчеты за указанный период.
        timely_filtered_reports: list[dict] = [
            weather_report
            for weather_report
            in resp
            if dt.datetime.strptime(
                weather_report['surinkimo_data'], "%Y-%m-%d %H:%M").replace(
                    tzinfo=lithuanian_timezone) >= start
            and dt.datetime.strptime(
                weather_report['surinkimo_data'], "%Y-%m-%d %H:%M").replace(
                    tzinfo=lithuanian_timezone) < end
        ]
        # Проверка, что хотя бы один отчет за указанный период есть.
        if timely_filtered_reports:
            return timely_filtered_reports
        raise WeatherDataException(
            error='out_of_timerange_error',
            message=f"The station's reports don't belong to {period}.")

    def save_weather_data(
        self,
        parsed_reports: list[dict]
    ):
        """
        Десериализовать массив словарей погодных данных
        и сохранить в базу.
        """
        serializer = ApiScraperWeatherDataSerializer(
            data=parsed_reports, many=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

    def get_earl_latest_reptime(
            self, parsed_reports: list[dict]) -> tuple[dt.datetime, int]:
        """
        Вернуть время самого раннего и самого позднего отчета станции,
        а также количество отчетов сохраняемых в базу.
        """
        # Местное время самого раннего отчета.
        earliest_report_time = parsed_reports[
                len(parsed_reports) - 1]['local']

        # Местное время самого позднего отчета.
        latest_report_time = parsed_reports[0]['local']

        # Количество отчетов.
        reports_count = len(parsed_reports)
        return earliest_report_time, latest_report_time, reports_count
