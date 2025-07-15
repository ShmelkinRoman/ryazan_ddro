from datetime import datetime

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from webscraper.models import Station, WeatherData
from .serializers import StationSerializer, WeatherDataSerializer


class StationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class StationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class WeatherDataListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WeatherDataSerializer

    def get_queryset(self):
        queryset = WeatherData.objects.all()
        station_id = self.request.query_params.get('station_id')
        if station_id:
            queryset = queryset.filter(station__id=station_id)

        start_param = self.request.query_params.get('start')
        end_param = self.request.query_params.get('end')
        try:
            if start_param:
                start_dt = datetime.strptime(start_param, "%Y-%m-%dT%H:%M")
                queryset = queryset.filter(UTC__gte=start_dt)
            if end_param:
                end_dt = datetime.strptime(end_param, "%Y-%m-%dT%H:%M")
                queryset = queryset.filter(UTC__lte=end_dt)
        except (ValueError, TypeError):
            pass

        return queryset.order_by('-local')
