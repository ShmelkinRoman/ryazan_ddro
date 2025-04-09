from django.http import HttpResponse
from prometheus_client import generate_latest

from .metrics import record_ryazan_ddro_today_reports_counter


def metrics_view(request):
    # record_health_status()
    record_ryazan_ddro_today_reports_counter()
    return HttpResponse(generate_latest(), content_type='text/plain')
