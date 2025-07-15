from django.urls import path
from rest_framework.authtoken import views as auth_views

from .views import StationListView, StationDetailView, WeatherDataListView

urlpatterns = [
    path('stations/', StationListView.as_view(), name='stations-list'),
    path('stations/<int:pk>/', StationDetailView.as_view(), name='station-detail'),
    path('weather/', WeatherDataListView.as_view(), name='weather-list'),
    path('api-token-auth/', auth_views.obtain_auth_token, name='api-token-auth'),
]
