from django.db import models
from django.db.models import UniqueConstraint


class Station(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ddro_station_id = models.CharField(max_length=100, unique=False)
    ddro_station_name = models.CharField(max_length=200, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    position_change_counter = models.IntegerField(default=0)
    position_change_time = models.DateTimeField(null=True)


class WeatherData(models.Model):
    station = models.ForeignKey(Station, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)
    local = models.DateTimeField()  # Время снятия показаний по местному времени(Рязань(пояс UTC +3)).
    UTC = models.DateTimeField()  # Время снятия показаний по UTC.
    unix = models.BigIntegerField()  # Время снятия показаний по UTC в Unix.
    precipitation_type = models.CharField(null=True, max_length=100)
    surface_cond = models.CharField(null=True, max_length=100)
    friction_coeff = models.FloatField(null=True)
    humidity = models.FloatField(null=True)
    pressure = models.FloatField(null=True)
    temperature_air = models.FloatField(null=True)
    dew_point = models.FloatField(null=True)
    surface_temp = models.FloatField(null=True)
    water_layer_thickness = models.FloatField(null=True)
    snow_layer_thickness = models.FloatField(null=True)
    ice_layer_thickness = models.FloatField(null=True)
    ice_percentage = models.FloatField(null=True)
    wind_m_s_avg = models.FloatField(null=True)
    wind_degree = models.FloatField(null=True)
    precipitation_amount = models.FloatField(null=True)
    precipitation_delta = models.FloatField(null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['station', 'local'],
                name='station_localtime_unique_constraint',
                violation_error_message=(
                    'There should be only one weather report from '
                    'a station in a certain moment in time.'
                )
            )
        ]
