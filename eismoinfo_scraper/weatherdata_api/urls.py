from django.urls import path
from .views import (
     WeatherDataView, StationView, ParsingModelRetrieveUpdateView,
     ParsingModelCombinedReadView, ParsingModelListCreateView,
     CurrentWeatherDataView, StationRequestResultView,
     health_view
     )
from rest_framework.authtoken import views

urlpatterns = [
     path('health/', health_view, name='application-healthcheck'),
     path('get-weather-data/', WeatherDataView.as_view(),
          name='get-weather-data'),
     path('get-current-weather/', CurrentWeatherDataView.as_view(),
          name='get-current-weather'),
     path('get-stations/', StationView.as_view(), name='get-stations'),
     path('api-token-auth/', views.obtain_auth_token, name='get-token'),
     path('parsing-models/show-all/', ParsingModelCombinedReadView.as_view(),
          name='parsing-models-show-all'),
     path('parsing-models/<str:modelname>/', ParsingModelListCreateView.as_view(),
          name='parsing-models-list-create'),
     path('parsing-models/<str:modelname>/<int:id>/', ParsingModelRetrieveUpdateView.as_view(),
          name='parsing-models-retrieve-update'),
     path('station-request-results/', StationRequestResultView.as_view(), name='station-request-results')
]
