from django.db import models
import datetime as dt


class Station(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    eismo_station_id = models.PositiveIntegerField(unique=True)
    city_name = models.CharField(max_length=200)
    road_name = models.CharField(max_length=200)
    road_number = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()  # если меняется, то position_change_counter, LAST_CHANGE_TIME
    position_change_counter = models.IntegerField(default=0)
    position_change_time = models.DateTimeField(default=None, null=True)
    height = models.FloatField(default=None, null=True)


class StationRequestResult(models.Model):
    "Отчет по результату запроса к станции."
    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS'
        HTTP_REQUEST_ERROR = 'HTTP_REQUEST_ERROR'
        EMPTY_REPORT_ERROR = 'EMPTY_REPORT_ERROR'
        JSON_DECODE_ERROR = 'JSON_DECODE_ERROR'
        OUT_OF_TIMERANGE_ERROR = 'OUT_OF_TIMERANGE_ERROR'
        PARSING_ERROR = 'PARSING_ERROR'
        VALIDATION_ERROR = 'VALIDATION_ERROR'
        UNKNOWN_PARSING_VALUES_ERROR = 'UNKN_PARSING_ERROR'

        @classmethod
        def get_status_values(cls):
            return [status.value for status in cls]

    station = models.ForeignKey(
        Station,
        on_delete=models.DO_NOTHING,
        related_name='station_requests'
    )
    request_time = models.DateTimeField(auto_now_add=True, max_length=200)
    request_time_unix = models.PositiveIntegerField()
    status = models.CharField(
        choices=Status.choices,
        max_length=200
    )
    error_message = models.TextField(max_length=5000, blank=True, null=True)
    earliest_report_time = models.DateTimeField(blank=True, null=True, max_length=200)
    latest_report_time = models.DateTimeField(blank=True, null=True, max_length=200)
    reports_count = models.PositiveSmallIntegerField(default=0, null=True)

    def save(self, *args, **kwargs):
        if not self.request_time_unix:
            self.request_time_unix = int(dt.datetime.now().timestamp())
        super().save(*args, **kwargs)


class BaseCondition(models.Model):
    code = models.IntegerField(null=True, default=None)
    value_api = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=True, default=None)

    class Meta:
        abstract = True


class PrecipitationType(BaseCondition):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['value_api'],
                violation_error_message='This value_api already exists in the database!',
                name='unique_precipitation_value_api'
            )
        ]


class SurfaceCondition(BaseCondition):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['value_api'],
                violation_error_message='This value_api already exists in the SurfaceCondition!',
                name='unique_surfacecond_value_api'
            )
        ]


class WindDegree(BaseCondition):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['value_api'],
                violation_error_message='This value_api already exists in the WindDegree!',
                name='unique_winddegree_value_api'
            )
        ]

    def save(self, *args, **kwargs):
        # Если приходит число(градусы),
        # то сохраняем их.
        # Если направление ветра словом,
        # сохраняем соотв. ему градусы.
        if not self.code:
            try:
                self.code = int(self.value_api)
            except ValueError:
                self.code = None
        super().save(*args, **kwargs)


class WeatherData(models.Model):
    station = models.ForeignKey(
        Station, on_delete=models.DO_NOTHING,
        related_name='weather_data'
    )
    unix = models.PositiveIntegerField()  # По UTC, приходит от API.
    local = models.DateTimeField()  # Меняется с UTC +2 на UTC +3 30 марта 2025 до последнего воскр октября в контексте приложения автоматически.
    UTC = models.DateTimeField()  # Расчитывается из unix.
    time_zone_offset = models.IntegerField()  # = local - utc [minutes]
    created = models.DateTimeField(auto_now_add=True)
    surface_cond = models.IntegerField(null=True)
    temperature_air = models.FloatField(null=True)
    surface_temp = models.FloatField(null=True)
    visibility = models.IntegerField(null=True)
    wind_degree = models.IntegerField(null=True)
    wind_m_s_avg = models.FloatField(null=True)
    wind_m_s_max = models.FloatField(null=True)
    precipitation_type = models.IntegerField(null=True)
    precipitation_amount = models.FloatField(null=True)
    dew_point = models.FloatField(null=True)
    frost_point = models.FloatField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['station', 'unix'],
                name='station_unix_unique_constraint'
            )
        ]
