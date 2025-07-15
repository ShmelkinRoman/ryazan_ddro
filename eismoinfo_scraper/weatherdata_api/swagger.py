from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="weatherdata_api",
        default_version='v1',
        description="API для получения текущих и архивных погодных данных от станций ресурса eismoinfo.lt"
    ),
    public=True,
    permission_classes=(permissions.AllowAny,)
)
