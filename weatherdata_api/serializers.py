from rest_framework import serializers

from webscraper.models import Station, WeatherData


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = [
            'id',
            'ddro_station_id',
            'ddro_station_name',
            'latitude',
            'longitude',
            'position_change_counter',
            'position_change_time',
        ]


class WeatherDataSerializer(serializers.ModelSerializer):
    """Сериализатор для выдачи погодных данных без вложенной информации о станции."""

    class Meta:
        model = WeatherData
        exclude = ['station']
