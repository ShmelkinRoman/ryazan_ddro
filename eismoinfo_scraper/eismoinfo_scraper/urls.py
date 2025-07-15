
from django.contrib import admin
from django.urls import path, include
from weatherdata_api.swagger import schema_view

urlpatterns = [
    path('lt/admin/', admin.site.urls),
    path('lt/api/v1/', include('weatherdata_api.urls')),
    path('lt/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('lt/prometheus/', include('prometheus.urls'))
]
