from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from webscraper import tasks as ws_tasks

TASKS_MAP = {
    'update_stations': ('Обновить станции', ws_tasks.update_stations.delay),
    'save_weather_data': ('Сохранить погоду', ws_tasks.save_weather_data.delay),
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
