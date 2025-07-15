from django.http import HttpResponse
from prometheus_client import generate_latest

from .metrics import record_today_request_counter, record_health_status


def metrics_view(request):
    record_health_status()
    record_today_request_counter()
    return HttpResponse(generate_latest(), content_type='text/plain')
