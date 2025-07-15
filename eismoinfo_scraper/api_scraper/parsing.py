import math
import datetime as dt

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from typing import NamedTuple

from .models import (
    Station, PrecipitationType,
    SurfaceCondition, WindDegree
)

from .loggers import get_logger

logger = get_logger(__name__)


class ParsingModelTuple(NamedTuple):
    """
    A tuple that contains a parsing model class,
    its existing queryset and a collection of unknown API values
    obtained during the last parsing, that have to be assigned with a code.
    """
    model: type
    queryset: QuerySet
    unregistered_values: set


class DataComplianceTuple(NamedTuple):
    """
    A tuple that represents the compliance between an eismo JSON dict key,
    database filedname and the anticipated Python datatype.
    """
    eismo_key: str
    db_fieldname: str
    target_type: callable


class WeatherDictParser:
    """
    Класс для парсинга словаря от API в формат БД.
    """

    PARSING_MODELS_DICT = {
        'precipitation_type': ParsingModelTuple(
            model=PrecipitationType,
            queryset=PrecipitationType.objects.all(),
            unregistered_values=set()
        ),
        'surface_cond': ParsingModelTuple(
            model=SurfaceCondition,
            queryset=SurfaceCondition.objects.all(),
            unregistered_values=set()
        ),
        'wind_degree': ParsingModelTuple(
            model=WindDegree,
            queryset=WindDegree.objects.all(),
            unregistered_values=set()
        )
    }

    DATA_COMPLIANCE = [
        DataComplianceTuple("id", "eismo_station_id", int),
        DataComplianceTuple("surinkimo_data_unix", "unix", int),
        DataComplianceTuple("surinkimo_data", "local", dt.datetime),
        DataComplianceTuple("kelio_danga", "surface_cond", None),
        DataComplianceTuple("oro_temperatura", "temperature_air", float),
        DataComplianceTuple("dangos_temperatura", "surface_temp", float),
        DataComplianceTuple("matomumas", "visibility", int),
        DataComplianceTuple("vejo_kryptis", "wind_degree", None),
        DataComplianceTuple("vejo_greitis_vidut", "wind_m_s_avg", float),
        DataComplianceTuple("vejo_greitis_maks", "wind_m_s_max", float),
        DataComplianceTuple("krituliu_tipas", "precipitation_type", None),
        DataComplianceTuple("krituliu_kiekis", "precipitation_amount", float),
        DataComplianceTuple("rasos_taskas", "dew_point", float),
        DataComplianceTuple("uzsalimo_taskas", "frost_point", float)
    ]

    def __init__(
            self,
            mode: str,
            data_compliance_arr: list[DataComplianceTuple] = None,
            parsing_models_dict: dict[ParsingModelTuple] = None
            ):
        self.mode = mode
        if data_compliance_arr is None:
            data_compliance_arr = self.DATA_COMPLIANCE
        self.data_compliance_arr = data_compliance_arr

        if parsing_models_dict is None:
            parsing_models_dict = self.PARSING_MODELS_DICT
        self.parsing_models_dict = parsing_models_dict

        # Станции, которые повторно опрашиваем,
        # когда от них пришли неизвестные значения.
        self.stations_to_refetch = set()

    def update_parsing_models(self):
        """
        Внести новые значения в соответствующие парсинговые модели.
        """
        for db_fieldname, parsing_model_tuple in self.parsing_models_dict.items():
            if parsing_model_tuple.unregistered_values == set():
                logger.info(f'{db_fieldname}: no unregistered values received')
            else:
                logger.warning(f'{db_fieldname}: unregistered values: {parsing_model_tuple.unregistered_values}')
                for unregistered_value in parsing_model_tuple.unregistered_values:
                    parsing_model_tuple.model.objects.create(value_api=unregistered_value)
        logger.info('Adding unregistered values to the parsing models completed.')

    def parse_value(self, db_fieldname, target_type, value, station):
        """
        Преобразовать значение, полученное от api в ожидаемый тип данных
        Python или присвоить код явления. При отсутствии значения в
        парсинговой модели в данное поле сохранится null.
        """

        if value is None:
            return None
        elif target_type is None:
            # Получить объекты соответствующей парсинговой модели.
            queryset = self.parsing_models_dict[db_fieldname].queryset


            # Вернуть код первого совпадения с парсинговой моделью или None.
            matching_entry = next((entry for entry in queryset if entry.value_api == value), None)

            if matching_entry:
                return matching_entry.code
            elif db_fieldname == 'wind_degree':
                try:
                    parsed_value = int(value)
                except ValueError:
                    # Добавить неизвестное значение в список для присвоения кода.
                    self.parsing_models_dict[db_fieldname].unregistered_values.add(value)
                    # Добавить станцию в список для повторного опроса.
                    self.stations_to_refetch.add(station.eismo_station_id)
                    return None
                else:
                    # Добавить неизвестное значение в список для присвоения кода.
                    self.parsing_models_dict[db_fieldname].unregistered_values.add(value)
                    # Добавить станцию в список для повторного опроса.
                    self.stations_to_refetch.add(station.eismo_station_id)

            else:
                # Добавить неизвестное значение в список для присвоения кода.
                self.parsing_models_dict[db_fieldname].unregistered_values.add(value)
                # Добавить станцию в список для повторного опроса.
                self.stations_to_refetch.add(station.eismo_station_id)
                return None

        elif target_type == dt.datetime:
            parsed_value = dt.datetime.strptime(value, "%Y-%m-%d %H:%M")  # ValueError, TypeError
            return parsed_value
        else:
            parsed_value = target_type(value)  # ValueError, TypeError
            return parsed_value

    def parse_retrospective_report(self, station: Station, eismo_report: dict) -> dict:
        """
        Преобразовать словарь ретроспективных погодных данных, полученный
        от api, в словарь формата базы данных.
        """
        parsed_report = {}
        # ValueError, TypeError
        for data_compliance_tuple in self.data_compliance_arr:
            value = eismo_report[data_compliance_tuple.eismo_key]  # KeyError
            parsed_report[data_compliance_tuple.db_fieldname] = self.parse_value(
                db_fieldname=data_compliance_tuple.db_fieldname,
                target_type=data_compliance_tuple.target_type,
                value=value,
                station=station
            )
        parsed_report['station'] = station.pk  # ForeignKey на Station.
        parsed_report['UTC'] = dt.datetime.fromtimestamp(parsed_report['unix'])
        parsed_report['time_zone_offset'] = math.ceil(((parsed_report['local'] - parsed_report['UTC']).total_seconds()) / 60)
        return parsed_report

    def parse_current_report(self, eismo_report: dict) -> dict:
        """
        Преобразовать словарь текущих погодных данных, полученный
        от api, в словарь формата базы данных.
        """
        parsed_report = {}
        # ValueError, TypeError
        for data_compliance_tuple in self.data_compliance_arr:
            station = Station.objects.get(
                eismo_station_id=eismo_report['id']
            )
            value = eismo_report[data_compliance_tuple.eismo_key]  # KeyError
            parsed_report[data_compliance_tuple.db_fieldname] = self.parse_value(
                data_compliance_tuple.db_fieldname,
                data_compliance_tuple.target_type,
                value,
                station
            )
        parsed_report['station'] = station.pk
        parsed_report['UTC'] = dt.datetime.fromtimestamp(parsed_report['unix'])
        parsed_report['time_zone_offset'] = math.ceil(((parsed_report['local'] - parsed_report['UTC']).total_seconds()) / 60)
        return parsed_report

    def parse_current_weather_on_the_go(self, eismo_report: dict) -> dict:
        """
        Преобразовать словарь текущих погодных данных, полученный
        от api, в словарь формата базы данных.
        """
        parsed_report = {}
        # ValueError, TypeError
        for data_compliance_tuple in self.data_compliance_arr:
            station = Station.objects.get(
                eismo_station_id=eismo_report['id']
            )
            value = eismo_report[data_compliance_tuple.eismo_key]  # KeyError
            parsed_report[data_compliance_tuple.db_fieldname] = self.parse_value(
                data_compliance_tuple.db_fieldname,
                data_compliance_tuple.target_type,
                value,
                station
            )
        parsed_report['station'] = station.pk
        # Для текущей погоды нужны eismo_station_id, latitude и longitude
        # сразу в словаре.
        parsed_report['latitude'] = station.latitude
        parsed_report['longitude'] = station.longitude
        parsed_report['height'] = station.height
        parsed_report[
            'position_change_counter'] = station.position_change_counter
        parsed_report[
            'position_change_time'] = station.position_change_time
        parsed_report['UTC'] = dt.datetime.fromtimestamp(parsed_report['unix'])
        parsed_report['time_zone_offset'] = math.ceil(((parsed_report['local'] - parsed_report['UTC']).total_seconds()) / 60)
        return parsed_report

    def get_parsed_weather_reports(
        self,
        eismo_reports: list[dict],
        station: Station = None,
    ) -> list[dict]:
        """
        Преобразовать массив словарей в формат базы данных.
        """
        parsed_weather_reports = []
        for eismo_report in eismo_reports:
            if self.mode == 'retrospective':
                parsed_report = self.parse_retrospective_report(
                    station=station,
                    eismo_report=eismo_report
                )
                parsed_weather_reports.append(parsed_report)
            elif self.mode == 'current':
                parsed_report = self.parse_current_report(
                    eismo_report=eismo_report
                )
            elif self.mode == 'current_weather_parsing':
                parsed_report = self.parse_current_weather_on_the_go(
                    eismo_report=eismo_report
                )
                parsed_weather_reports.append(parsed_report)
        return parsed_weather_reports
