from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from webscraper import tasks as ws_tasks
from eismoinfo_scraper.api_scraper import tasks as api_tasks

TASKS_MAP = {
    'update_stations': ('Обновить станции', ws_tasks.update_stations.delay),
    'save_weather_data': ('Сохранить погоду', ws_tasks.save_weather_data.delay),
    'api_update_stations': ('API обновить станции', api_tasks.update_stations.delay),
    'api_update_heights': ('API обновить высоты', api_tasks.update_station_heights.delay),
    'api_save_current': ('API текущая погода', api_tasks.save_current_weather_data.delay),
    'api_save_last_hour': ('API погода за последний час', api_tasks.save_weather_data_last_hour.delay),
    'api_save_last_day': ('API погода за последний день', api_tasks.save_weather_data_last_day.delay),
}


@staff_member_required
def task_list_view(request):
    if request.method == 'POST':
        task_name = request.POST.get('task')
        task = TASKS_MAP.get(task_name)
        if task:
            task[1]()
        return redirect(reverse('task_list'))
    return render(request, 'task_list.html', {'tasks': TASKS_MAP})
