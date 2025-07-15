from rest_framework import serializers
from api_scraper.models import WeatherData, Station, StationRequestResult
from django.db.models import QuerySet


class WeatherDataReadSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    eismo_station_id = serializers.IntegerField()
    height = serializers.FloatField(allow_null=True)
    position_change_counter = serializers.IntegerField()
    position_change_time = serializers.DateTimeField(allow_null=True)

    class Meta:
        model = WeatherData
        fields = [
            "eismo_station_id",
            "latitude",
            "longitude",
            "height",
            "position_change_counter",
            "position_change_time",
            'unix',
            'local',
            'UTC',
            'time_zone_offset',
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


class CurrentWeatherDataReadSerializer(serializers.Serializer):
    """Сериализатор для чтения текущих погодных данных."""

    eismo_station_id = serializers.IntegerField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    height = serializers.FloatField(allow_null=True)
    position_change_counter = serializers.IntegerField()
    position_change_time = serializers.DateTimeField(allow_null=True)
    unix = serializers.IntegerField(allow_null=True)  # По стандарту UTC
    local = serializers.DateTimeField(allow_null=True)  # Меняется с UTC +2 на UTC +3 30 марта 2025 до последнего воскр октября в контексте приложения автоматически.
    UTC = serializers.DateTimeField(allow_null=True)  # Расчитывается из unix.
    time_zone_offset = serializers.IntegerField(allow_null=True)  # =local - utc [minutes]
    surface_cond = serializers.IntegerField(allow_null=True)
    temperature_air = serializers.FloatField(allow_null=True)
    surface_temp = serializers.FloatField(allow_null=True)
    visibility = serializers.IntegerField(allow_null=True)
    wind_degree = serializers.IntegerField(allow_null=True)
    wind_m_s_avg = serializers.FloatField(allow_null=True)
    wind_m_s_max = serializers.FloatField(allow_null=True)
    precipitation_type = serializers.IntegerField(allow_null=True)
    precipitation_amount = serializers.FloatField(allow_null=True)
    dew_point = serializers.FloatField(allow_null=True)
    frost_point = serializers.FloatField(allow_null=True)


class StationSerializer(serializers.ModelSerializer):
    """Сериализатор для простомотра данных станций."""

    class Meta:
        model = Station
        fields = [
            'eismo_station_id',
            'city_name',
            'road_name',
            'road_number',
            'latitude',
            'longitude',
            'height',
            'position_change_counter',
            'position_change_time'
        ]


class ParsingModelListCreateRetrieveSerializer(serializers.Serializer):
    """Сериализватор для чтения и создания объектов парсиговой модели."""

    id = serializers.IntegerField(source='pk', read_only=True)
    code = serializers.IntegerField(allow_null=True, required=False)
    value_api = serializers.CharField(required=True)
    description = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = None
        fields = ['id', 'code', 'value_api', 'description']

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    @classmethod
    def set_model(cls, model):
        cls.Meta.model = model


class ParsingModelUpdateSerializer(serializers.Serializer):
    """Сериализатор для обновления объектов парсинговой модели."""

    id = serializers.IntegerField(source='pk', read_only=True)
    code = serializers.IntegerField(allow_null=False, required=True)
    value_api = serializers.CharField(required=False)
    description = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = None
        fields = ['id', 'code', 'value_api', 'description']

    def update(self, instance, validated_data):
        instance.code = validated_data.get('code', instance.code)
        instance.value_api = validated_data.get('value_api', instance.value_api)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance

    @classmethod
    def set_model(cls, model):
        cls.Meta.model = model


class ParsingModelReadSerializer(serializers.Serializer):
    """Вспомогательный сериализатор для чтения каждой парсинговой модели."""

    id = serializers.IntegerField()
    code = serializers.IntegerField(allow_null=True)
    value_api = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)


class ParsingModelCombinedReadSerializer(serializers.Serializer):
    """Сериализатор для чтения всех парсинговых моделей одновременно."""

    precipitation_type = ParsingModelReadSerializer(many=True)
    surface_cond = ParsingModelReadSerializer(many=True)
    wind_degree = ParsingModelReadSerializer(many=True)


class StationRequestResultSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра результатов опроса станций."""
    eismo_station_id = serializers.IntegerField()

    class Meta:
        model = StationRequestResult
        fields = [
            'eismo_station_id',
            'request_time',
            'status',
            'error_message',
            'earliest_report_time',
            'latest_report_time',
            'reports_count'
        ]