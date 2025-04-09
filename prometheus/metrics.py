# import requests

from prometheus_client import Gauge
from webscraper.models import WeatherData
import datetime as dt

last_reset_date = dt.datetime.today().date()

ryazan_ddro_today_reports_counter = Gauge(
        'ryazan_ddro_today_reports_counter',
        "Today's number of weather reports saved to db.",
        ['status']
    )

# ryazan_ddro_health_status = Gauge(
#     'health_status',
#     "1 if the service is healthy, 0 if it's unhealthy"
# )


# def record_health_status():
#     global health_status
#     try:
#         if requests.get('http://eismoinfo-app:8000/ddro/api/v1/health').status_code == 200:
#             health_status.set(1)
#         else:
#             health_status.set(0)
#     except Exception:
#         health_status.set(0)


def record_ryazan_ddro_today_reports_counter():
    global last_reset_date
    global ryazan_ddro_today_reports_counter
    today = dt.datetime.today().date()

    if today != last_reset_date:
        ryazan_ddro_today_reports_counter.clear()
        last_reset_date = today

    ryazan_ddro_today_reports_counter.labels(status='SUCCESS').set(
        WeatherData.objects.filter(
            UTC__date=dt.datetime.today().date()
        ).count()
    )
