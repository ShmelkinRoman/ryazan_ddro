from rest_framework import serializers

from .models import WeatherData


class ApiScraperWeatherDataSerializer(serializers.ModelSerializer):
    """Сериализатор для сохранения ретроспективных данных в базу."""

    class Meta:
        model = WeatherData
        fields = [
            "station",  # UniqueTogether constraint(station, unix) applied automatically. Raises 400.
            "unix",
            "local",
            "UTC",
            "time_zone_offset",
            "created",
            "surface_cond",
            "temperature_air",
            "surface_temp",
            "visibility",
            "wind_degree",
            "wind_m_s_avg",
            "wind_m_s_max",
            "precipitation_type",
            "precipitation_amount",
            "dew_point",
            "frost_point"
        ]
