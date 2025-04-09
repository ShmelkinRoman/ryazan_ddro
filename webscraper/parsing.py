from django.db.models import QuerySet
from typing import NamedTuple
import datetime as dt
from .logging import get_logger
from zoneinfo import ZoneInfo

# Логгирование.
logger = get_logger(__name__)


class ParsingModelTuple(NamedTuple):
    """
    A tuple that represents a parsing model class,
    its corresponding queryset and the collection of unknown API values
    obtained during the last import session.
    """
    model: type
    queryset: QuerySet
    unregistered_values: set


class DataComplianceTuple(NamedTuple):
    """
    A tuple that represents the compliance between the source's dict key,
    a corresponding database fieldname and the anticipated Python datatype.
    """
    db_fieldname: str
    target_type: callable


DATA_COMPLIANCE = [
        DataComplianceTuple("ddro_station_id", str),
        DataComplianceTuple("ddro_station_name", str),
        DataComplianceTuple("latitude", float),
        DataComplianceTuple("longitude", float),
        DataComplianceTuple("local", dt.datetime),
        DataComplianceTuple("precipitation_type", str),
        DataComplianceTuple("surface_cond", str),  # в дорожной модели.
        DataComplianceTuple("friction_coeff", float),  # в дорожной модели.
        DataComplianceTuple("humidity", float),
        DataComplianceTuple("pressure", float),
        DataComplianceTuple("temperature_air", float),
        DataComplianceTuple("dew_point", float),
        DataComplianceTuple("surface_temp", float),
        DataComplianceTuple("water_layer_thickness", float),
        DataComplianceTuple("snow_layer_thickness", float),
        DataComplianceTuple("ice_layer_thickness", float),
        DataComplianceTuple("ice_percentage", float),
        DataComplianceTuple("wind_m_s_avg", float),
        DataComplianceTuple("wind_degree", float),
        DataComplianceTuple("precipitation_amount", float),
        DataComplianceTuple("precipitation_delta", float)
    ]


class WeatherDictParser:
    def __init__(self, data_compliance_arr=DATA_COMPLIANCE):
        self.data_compliance_arr = data_compliance_arr

    def parse_value(self, db_fieldname: str, target_type: callable, value: str):
        """
        Parse value according to its target data type.
        """

        if value in [None, ""]:
            parsed_value = None
        # elif target_type is None:
        #     # Получить объекты соответствующей парсинговой модели.
        #     queryset = self.parsing_models_dict[db_fieldname].queryset


        #     # Вернуть код первого совпадения с парсинговой моделью или None.
        #     matching_entry = next((entry for entry in queryset if entry.value_api == value), None)

        #     if matching_entry:
        #         return matching_entry.code
        #     elif db_fieldname == 'wind_degree':
        #         try:
        #             parsed_value = int(value)
        #         except ValueError:
        #             # Добавить неизвестное значение в список для присвоения кода.
        #             self.parsing_models_dict[db_fieldname].unregistered_values.add(value)
        #             # Добавить станцию в список для повторного опроса.
        #             self.stations_to_refetch.add(station.eismo_station_id)
        #             return None
        #         else:
        #             # Добавить неизвестное значение в список для присвоения кода.
        #             self.parsing_models_dict[db_fieldname].unregistered_values.add(value)
        #             # Добавить станцию в список для повторного опроса.
        #             self.stations_to_refetch.add(station.eismo_station_id)

        #     else:
        #         # Добавить неизвестное значение в список для присвоения кода.
        #         parsing_model_tuple.unregistered_values.add(value)
        #         # Добавить станцию в список для повторного опроса.
        #         self.stations_to_refetch.add(station.eismo_station_id)
        #         return None
        elif target_type == dt.datetime:
            parsed_value: dt.datetime = dt.datetime.strptime(value, "%d.%m.%Y %H:%M:%S")  # ValueError, TypeError
        else:
            parsed_value = target_type(value)  # ValueError, TypeError
        return parsed_value

    def parse_weather_report(self, weather_report: dict[str, str]) -> dict:
        """
        Parse raw weather report dict into the database suitable format.
        """
        parsed_report = {}
        # ValueError, TypeError
        for data_compliance_tuple in self.data_compliance_arr:
            value = weather_report[data_compliance_tuple.db_fieldname]  # забрать значение в виде строки.
            try:
                parsed_report[data_compliance_tuple.db_fieldname] = self.parse_value(
                    db_fieldname=data_compliance_tuple.db_fieldname,
                    target_type=data_compliance_tuple.target_type,
                    value=value
                )
            except ValueError as e:
                logger.warning(f'Station {weather_report["ddro_station_name"]}'
                               f'{data_compliance_tuple.db_fieldname}: {value}, error {e}. ')
                parsed_report[data_compliance_tuple.db_fieldname] = None

        # Добавить UTC(datetime и unix).
        parsed_report['UTC'] = (parsed_report['local'] - dt.timedelta(hours=3)).astimezone(ZoneInfo('UTC'))
        parsed_report['local'] = parsed_report['UTC'].astimezone(ZoneInfo('Europe/Moscow'))
        parsed_report['unix'] = int(parsed_report['UTC'].timestamp())
        return parsed_report

    def get_parsed_weather_reports(self, weather_reports_arr: list[dict]):
        parsed_reports = []
        for weather_report in weather_reports_arr:
            parsed_report = self.parse_weather_report(weather_report)
            parsed_reports.append(parsed_report)
        print('Parsed weather reports count =', len(parsed_reports))
        print('Parsed weather reports =', parsed_reports)
        return parsed_reports
