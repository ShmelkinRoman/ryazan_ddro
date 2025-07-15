import datetime as dt

from django.db.models import F
from django.db import IntegrityError

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.exceptions import ValidationError
from api_scraper.models import (
    WeatherData, Station, PrecipitationType,
    WindDegree, SurfaceCondition,
    StationRequestResult
)
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from api_scraper.loggers import get_logger
from api_scraper.weather_data_service import WeatherDataService
from api_scraper.station_request_result import StationRequestResultQueryService

from .serializers import (
    WeatherDataReadSerializer,
    StationSerializer,
    ParsingModelListCreateRetrieveSerializer,
    ParsingModelUpdateSerializer,
    ParsingModelCombinedReadSerializer,
    CurrentWeatherDataReadSerializer,
    StationRequestResultSerializer
)

logger = get_logger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_view(request):
    """
    Класс для проверки работоспособности приложения.
    """
    return Response({'status': 'OK'}, status=status.HTTP_200_OK)


class WeatherDataView(generics.GenericAPIView):
    """
    Класс для просмотра архивных погодных данных.
    Обязательные query parameters: start, end.
    """

    serializer_class = WeatherDataReadSerializer
    timezone = 'Europe/Vilnius'
    permission_classes = [IsAuthenticated,]

    def get_queryset(self, params):
        queryset = WeatherData.objects.filter(**params).select_related(
            'station').annotate(
                eismo_station_id=F('station__eismo_station_id'),
                latitude=F('station__latitude'),
                longitude=F('station__longitude'),
                height=F('station__height'),
                position_change_counter=F('station__position_change_counter'),
                position_change_time=F('station__position_change_time')
            ).order_by('eismo_station_id', '-local')
        return queryset

    @swagger_auto_schema(
        operation_description=('Посмотеть архивные погодные данные '
                               'по заданным параметрам.\nОбязательные query parameters: '
                               'start, end. Опционально: id(станции) '),
        responses={
            400: 'Ошибка: Параметр start позже end. \nОшибка: Неверный формат введенных значений'
        },

        manual_parameters=[
            openapi.Parameter('id', openapi.IN_QUERY,
                              description="ID станции",
                              type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('start', openapi.IN_QUERY,
                              description="Начало запрашиваемого периода по UTC,  формат: 2024-11-21Т10:00",
                              type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('end', openapi.IN_QUERY,
                              description="Конец запращиваемого периода по UTC, формат: 2024-11-21Т23:00",
                              type=openapi.TYPE_STRING, required=True)
        ])
    def get(self, request):
        #  Получить значение переданные в query params.
        #  и конвертировать в типы данных Python.
        params = {}
        try:
            station_id: list[str] = self.request.query_params.get('id', None)
            params['station__eismo_station_id'] = int(station_id)
        except (TypeError, ValueError):
            pass
        try:
            # Получить время начала запрашиваемого периода по UTC.
            start_param: list[str] = self.request.query_params.get(
                'start', None).split('T')
            start_date = dt.datetime.strptime(start_param[0], "%Y-%m-%d")
            start_time = dt.datetime.strptime(start_param[1], "%H:%M").time()
            params['UTC__gte'] = dt.datetime.combine(start_date, start_time)

            # Получить время конца запрашиваемого периода по UTC.
            end_param: list[str] = self.request.query_params.get(
                'end', None).split('T')
            end_date = dt.datetime.strptime(end_param[0], "%Y-%m-%d")
            end_time = dt.datetime.strptime(end_param[1], "%H:%M").time()
            params['UTC__lte'] = dt.datetime.combine(end_date, end_time)

        except (TypeError, ValueError):
            response_data = {
                'result': [],
                'count': 0,
                'status': ('Ошибка при конвертации введенных значений. '
                           'Требуемый формат параметров: /?id=71(опционально)&start=2024-11-21T10:00&end=2024-11-22T10:00')
            }
            return Response(
                response_data,
                status=status.HTTP_200_OK
            )
        # Проверка на корректность временных рамок.
        if params['UTC__gte'] > params['UTC__lte']:
            response_data = {
                'result': [],
                'count': 0,
                'status': ('Параметр start позже end.'
                           'Требуемый формат параметров: /?id=71(опционально)&start=2024-11-21T10:00&end=2024-11-22T10:00')
            }
            return Response(
                response_data,
                status=status.HTTP_200_OK
            )

        # Сделать запрос к базе.
        queryset = self.get_queryset(params)
        if queryset.exists():
            serializer = WeatherDataReadSerializer(queryset, many=True)
            response_data = {
                'result': serializer.data,
                'count': len(serializer.data),
                'status': 'success'
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(
                {'Ошибка': 'В базе данных отстутвуют данные '
                 'удовлетворяющие указанным параметам.'},
                status=status.HTTP_200_OK
        )


class CurrentWeatherDataView(generics.GenericAPIView):
    """
    Класс для просмотра фактических погодных данных.
    """
    serializer_class = CurrentWeatherDataReadSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
            operation_description='Посмотреть текущие погодные данные всех функционирующих на данный момент станций.'
    )
    def get(self, request):
        # Получить текущие отчеты погоды от всех станций.
        weather_data_service = WeatherDataService(mode='current_weather_parsing')
        parsed_reports = weather_data_service.fetch_current_weather()
        parsed_reports.sort(key=lambda x: x['eismo_station_id'])

        # Сериализовать данные и вернуть ответ.
        serializer = self.get_serializer(data=parsed_reports, many=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            response_data = {
                'result': [],
                'count': 0,
                'status': e
            }
        else:
            response_data = {
                'result': serializer.data,
                'count': len(serializer.data),
                'status': 'success'
            }
        return Response(response_data, status=status.HTTP_200_OK)  # serializer.data - сериализованные данные в формате БД.


class StationView(generics.GenericAPIView):
    """Класс для просмотра данных станций из БД."""
    serializer_class = StationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Station.objects.all().order_by('eismo_station_id')

    @swagger_auto_schema(
            operation_description='Посмотреть посмотеть информацию по всем станциям в БД.'
    )
    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ParsingModelCombinedReadView(generics.GenericAPIView):
    """Класс для просмотра данных всех парсинговых моделей одновременно."""

    serializer_class = ParsingModelCombinedReadSerializer
    permission_classes = [IsAuthenticated]

    def get_show_undefined_param(self):
        return self.request.query_params.get('show_undefined', 'false') == 'true'

    def get_queryset(self, modelname):
        show_undefined = self.get_show_undefined_param()
        match modelname:
            case 'precipitation-type':
                model = PrecipitationType
            case 'surface-cond':
                model = SurfaceCondition
            case 'wind-degree':
                model = WindDegree
        if show_undefined:
            return model.objects.filter(code=None)
        return model.objects.all()

    @swagger_auto_schema(
        operation_description='Отобразить записи всех парсинговых моделей из БД.',
        manual_parameters=[
            openapi.Parameter('show_undefined', openapi.IN_QUERY,
                              description="Показать только те записи, у которых отсутствует код явления: /?show_undefined=true",
                              type=openapi.TYPE_BOOLEAN, required=False)
        ])
    def get(self, request):
        precipitation_type_queryset = self.get_queryset(modelname='precipitation-type')
        surface_cond_queryset = self.get_queryset(modelname='surface-cond')
        wind_degree_queryset = self.get_queryset(modelname='wind-degree')

        # Converting QuerySets to lists of dictionaries
        precipitation_type_data = [item for item in precipitation_type_queryset.values()]
        surface_cond_data = [item for item in surface_cond_queryset.values()]
        wind_degree_data = [item for item in wind_degree_queryset.values()]
        print(wind_degree_data)

        # Creating the data dictionary for serialization
        data = {
            'precipitation_type': precipitation_type_data,
            'surface_cond': surface_cond_data,
            'wind_degree': wind_degree_data
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ParsingModelListCreateView(generics.GenericAPIView):
    """Класс для просмотра всех записей или создания новой записи в парсинговой модели."""

    serializer_class = ParsingModelListCreateRetrieveSerializer
    permission_classes = [IsAdminUser]
    allowed_methods = ['GET', 'POST']
    ordering = ['id']

    def get_show_undefined_param(self):
        return self.request.query_params.get('show_undefined', 'false') == 'true'

    def get_model(self, modelname):
        match modelname:
            case 'precipitation-type':
                model = PrecipitationType
            case 'surface-cond':
                model = SurfaceCondition
            case 'wind-degree':
                model = WindDegree
        return model

    def get_queryset(self, model):
        show_undefined = self.get_show_undefined_param()
        print('show undefined =', show_undefined)
        if show_undefined:
            return model.objects.filter(code=None)
        return model.objects.all()

    @swagger_auto_schema(
        operation_description=('Посмотреть все записи парсинговой модели из БД.\n'),
        manual_parameters=[
            openapi.Parameter(
                'modelname', openapi.IN_PATH,
                description=('Имя парсинговой модели\n'
                             'Модель погодных явлений: /precipitation-type/\n'
                             'Модель состояния дороги: /surface-cond/\n'
                             'Модель направления ветра: /wind-degree/\n'),
                type=openapi.TYPE_STRING, reqired=True
            ),
            openapi.Parameter('show_undefined', openapi.IN_QUERY,
                              description="Показать только те записи, у которых отсутствует код явления: /?show_undefined=true",
                              type=openapi.TYPE_BOOLEAN, required=False)
        ]
    )
    def get(self, request, modelname):
        model = self.get_model(modelname)
        queryset = self.get_queryset(model)
        serializer_class = self.get_serializer_class()
        serializer_class.set_model(model)
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description=('Добавить новую запись в парсинговую модель.\n'),
        manual_parameters=[
            openapi.Parameter(
                'modelname', openapi.IN_PATH,
                description=('Имя парсинговой модели\n'
                             'Модель погодных явлений: /precipitation-type/\n'
                             'Модель состояния дороги: /surface-cond/\n'
                             'Модель направления ветра: /wind-degree/\n'),
                type=openapi.TYPE_STRING, reqired=True
            )
        ]
    )
    def post(self, request, modelname):
        model = self.get_model(modelname)
        data = self.request.data
        serializer_class = self.get_serializer_class()
        serializer_class.set_model(model)
        serilizer = self.get_serializer(data=data)
        try:
            serilizer.is_valid(raise_exception=True)
            serilizer.save()
        except ValidationError as e:
            return Response(f'error: {e}', status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({'error': 'Объект с таким значением value_api уже существует в данной модели.'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({'created_obj': serilizer.data, 'message': 'Запись создана!'},
                        status=status.HTTP_201_CREATED)


class ParsingModelRetrieveUpdateView(generics.GenericAPIView):
    """Класс для просмотра, обновления или удаления записи в парсинговой модели."""

    serializer_class = ParsingModelUpdateSerializer
    permission_classes = [IsAdminUser]
    allowed_methods = ['GET', 'PUT', 'DELETE']
    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    def get_model(self, modelname):
        match modelname:
            case 'precipitation-type':
                model = PrecipitationType
            case 'surface-cond':
                model = SurfaceCondition
            case 'wind-degree':
                model = WindDegree
        return model

    @swagger_auto_schema(
        operation_description=('Посмотреть одну запись парсиноговой модели по ee id.'),
        manual_parameters=[
            openapi.Parameter(
                'modelname', openapi.IN_PATH,
                description=('Имя парсинговой модели\n'
                             'Модель погодных явлений: /precipitation-type/\n'
                             'Модель состояния дороги: /surface-cond/\n'
                             'Модель направления ветра: /wind-degree/\n'),
                type=openapi.TYPE_STRING, reqired=True
            ),
            openapi.Parameter(
                'id', openapi.IN_PATH, description='id объекта.',
                type=openapi.TYPE_INTEGER, reqired=True
            ),
        ]
    )
    def get(self, request, modelname, id):
        model = self.get_model(modelname)
        self.queryset = model.objects.all()
        obj = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer_class.set_model(model)
        serializer = serializer_class(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description=('Обновить запись парсиноговой модели по ee id.'),
        manual_parameters=[
            openapi.Parameter(
                'modelname', openapi.IN_PATH,
                description=('Имя парсинговой модели\n'
                             'Модель погодных явлений: /precipitation-type/\n'
                             'Модель состояния дороги: /surface-cond/\n'
                             'Модель направления ветра: /wind-degree/\n'),
                type=openapi.TYPE_STRING, reqired=True
            ),
            openapi.Parameter(
                'id', openapi.IN_PATH, description='id объекта.',
                type=openapi.TYPE_INTEGER, reqired=True
            )
        ]
    )
    def put(self, request, modelname, id):
        model = self.get_model(modelname)
        self.queryset = model.objects.all()
        obj = self.get_object()
        data = request.data
        serializer_class = self.get_serializer_class()
        serializer_class.set_model(model)
        serilizer = self.get_serializer(instance=obj, data=data)
        try:
            serilizer.is_valid(raise_exception=True)
            serilizer.save()
        except ValidationError as e:
            return Response(f'error: {e}', status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({'error': 'Объект с таким значением value_api уже существует в данной модели.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {'updated_obj': serilizer.data,
             'message': 'Запись обновлена!'},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description=('Удалить запись парсиноговой модели по ee id.'),
        manual_parameters=[
            openapi.Parameter(
                'modelname', openapi.IN_PATH,
                description=('Имя парсинговой модели\n'
                             'Модель погодных явлений: /precipitation-type/\n'
                             'Модель состояния дороги: /surface-cond/\n'
                             'Модель направления ветра: /wind-degree/\n'),
                type=openapi.TYPE_STRING, reqired=True
            ),
            openapi.Parameter(
                'id', openapi.IN_PATH, description='id объекта.',
                type=openapi.TYPE_INTEGER, reqired=True
            )
        ]
    )
    def delete(self, request, modelname, id):
        model = self.get_model(modelname)
        self.queryset = model.objects.all()
        obj = self.get_object()
        obj.delete()
        return Response(
            {'message': 'Запись удалена!'},
            status=status.HTTP_204_NO_CONTENT
        )


class StationRequestResultView(generics.GenericAPIView):
    """
    Класс для чтения результатов опроса станций.
    """
    serializer_class = StationRequestResultSerializer
    permission_classes = [IsAdminUser,]

    def get_queryset(self, params):
        service = StationRequestResultQueryService()
        queryset = service.get_request_results(**params).select_related(
            'station').annotate(
                eismo_station_id=F('station__eismo_station_id'),
            ).order_by('eismo_station_id')
        return queryset

    @swagger_auto_schema(
        operation_description=('Отборазить результаты опроса станции/станций за период времени.'),
        responses={
            400: 'Ошибка: Параметр start позже end. \nОшибка: Неверный формат введенных значений'
        },

        manual_parameters=[
            openapi.Parameter('id', openapi.IN_QUERY,
                              description='ID станции',
                              type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description=(
                    'статус запроса к станции, выбор из: \n'
                    '    1. success            - успешный запрос, данные сохранены.\n'
                    '    3. error              - все неуспешные запросы.\n'
                    '    2. http_request_error - ошибка при http запросе.\n'
                    '    4. empty_report_error - пустой ответ сервера(200 ОК).\n'
                    '    5. json_decode_error  - ошибка при декодировании JSON-строки.\n'
                    '    6. out_of_timerange_error   - отчеты, полученные в ответе, вне требуемого временного диапазона.\n'
                    '    7. parsing_error      - ошибка при преобразовании данных словарей в ожидаемые базой.\n'
                    '    8. validation_error   - вероятнее всего нарушена уникальность данных (станция - момент времени unix)\n'
                ), type=openapi.TYPE_STRING, required=False
            ),
            openapi.Parameter('start', openapi.IN_QUERY,
                              description="Начало запрашиваемого периода по UTC,  формат: 2024-11-21Т10:00",
                              type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('end', openapi.IN_QUERY,
                              description="Конец запращиваемого периода по UTC, формат: 2024-11-21Т23:00",
                              type=openapi.TYPE_STRING, required=True)
        ])
    def get(self, request):
        try:
            params = {}

            # Получить id станции(необязательный параметр).
            station_id: list[str] = self.request.query_params.get('id', None)
            if station_id:
                station_id = int(station_id)

            # Получить время начала запрашиваемого периода по UTC.
            start_param: list[str] = self.request.query_params.get(
                'start', None).split('T')
            start_date = dt.datetime.strptime(start_param[0], "%Y-%m-%d")
            start_time = dt.datetime.strptime(start_param[1], "%H:%M").time()
            start_datetime = dt.datetime.combine(start_date, start_time)

            # Получить время конца запрашиваемого периода по UTC.
            end_param: list[str] = self.request.query_params.get(
                'end', None).split('T')
            end_date = dt.datetime.strptime(end_param[0], "%Y-%m-%d")
            end_time = dt.datetime.strptime(end_param[1], "%H:%M").time()
            end_datetime = dt.datetime.combine(end_date, end_time)

            # Получить статус опроса станции(необязательный параметр).
            request_status = self.request.query_params.get('status', None)
            status_values_list = [
                status_value.lower()
                for status_value
                in StationRequestResult.Status.get_status_values()
            ]
            if (request_status in status_values_list) or request_status == 'error':
                request_status = request_status.upper()
            elif request_status is None:
                pass
            else:
                raise ValueError

        except (TypeError, ValueError, AttributeError):
            return Response(
                {'Ошибка': 'Ошибка при конвертации введенных значений.'
                 'Требуемый формат параметров: /?id=5(необязательный)&start='
                 '2024-11-21T10:00&end=2024-11-22T10:00&status(необязательный)=SUCCESS'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Проверка на корректность временных рамок.
        if start_datetime > end_datetime:
            return Response(
                {'Ошибка': ' Параметр start позже end.'
                 'Требуемый формат параметров: /?id=5&start=2024-11-21 10:00&end=2024-11-22 10:00'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создать словарь с фильтрами.
        params = {
            'start': start_datetime,
            'end': end_datetime,
            'station_id': station_id,
            'request_status': request_status
        }
        print(params)
        # Сделать запрос к базе.
        queryset = self.get_queryset(params)

        # Сериализовать ответ, если не пустой.
        if queryset.exists():
            serializer = StationRequestResultSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
                {'Ошибка': 'В базе данных отстутвуют данные '
                 'удовлетворяющие указанным параметам.'},
                status=status.HTTP_200_OK
        )
