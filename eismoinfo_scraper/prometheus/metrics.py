import requests

from prometheus_client import Gauge
from api_scraper.models import StationRequestResult
import datetime as dt

last_reset_date = dt.datetime.today().date()

today_request_counter = Gauge(
        'today_request_counter',
        "Today's number of requests according to their status",
        ['status']
    )

health_status = Gauge(
    'health_status',
    "1 if the service is healthy, 0 if it's unhealthy"
)


def record_health_status():
    global health_status
    try:
        if requests.get('http://eismoinfo-app:8000/lt/api/v1/health').status_code == 200:
            health_status.set(1)
        else:
            health_status.set(0)
    except Exception:
        health_status.set(0)


def record_today_request_counter():
    global last_reset_date
    global today_request_counter
    today = dt.datetime.today().date()

    if today != last_reset_date:
        today_request_counter.clear()
        last_reset_date = today

    today_request_counter.labels(status='SUCCESS').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status__icontains='SUCCESS'
        ).count()
    )

    today_request_counter.labels(status='TOTAL').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date()
        ).count()
    )

    today_request_counter.labels(status='FAILED').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status__icontains='ERROR'
        ).count()
    )

    today_request_counter.labels(status='UNKNOWN_PARSING_VALUE_ERROR').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status='UNKN_PARSING_ERROR'
        ).count()
    )

    today_request_counter.labels(status='HTTP_REQUEST_ERROR').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status='HTTP_REQUEST_ERROR'
        ).count()
    )

    today_request_counter.labels(status='EMPTY_REPORT_ERROR').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status='EMPTY_REPORT_ERROR'
        ).count()
    )

    today_request_counter.labels(status='JSON_DECODE_ERROR').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status='JSON_DECODE_ERROR'
        ).count()
    )

    today_request_counter.labels(status='OUT_OF_TIMERANGE_ERROR').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status='OUT_OF_TIMERANGE_ERROR'
        ).count()
    )

    today_request_counter.labels(status='PARSING_ERROR').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status='PARSING_ERROR'
        ).count()
    )

    today_request_counter.labels(status='VALIDATION_ERROR').set(
        StationRequestResult.objects.filter(
            request_time__date=dt.datetime.today().date(),
            status='VALIDATION_ERROR'
        ).count()
    )
