from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Weather Data API",
        default_version='v1',
        description="API для чтения данных с метеостанций DDRO",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
