from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import logging
from django.db import connection
from App.models import Task


logger = logging.getLogger(__name__)

@csrf_exempt
def get_tasks(request):
    
    try:
        tasks = Task.objects.all()
        tasks_data = []

        # Serialize tasks into a list of dictionaries
        for task in tasks:
            tasks_data.append({
                'id': task.id,
                'Title': task.title,
                'About': task.about,
                'DateAdded': task.date_added,
                'Deadline': task.deadline,
                'Status': task.status,
            })

        return JsonResponse({'tasks': tasks_data}, safe=False)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def index(request):
    
    return render(request, 'index.html')

@csrf_exempt
def create_task(request):
    
    if request.method == 'POST':
        logger.debug('POST request received')
        try:
            data = json.loads(request.body)
            task = data.get('task')
            about = data.get('about')
            date = data.get('date')
            logger.debug(f'Task: {task}, About: {about}, Date: {date}')
            if  task and about and  date:


                task = Task(
                    title=data.get('task'),
                    about=about,
                    deadline=date,
                    status="True"
                )
                task.save()
            return HttpResponseRedirect('/')
        except json.JSONDecodeError:
            logger.error('Invalid JSON')
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    logger.debug('GET request received')
    return render(request, 'index.html')

@csrf_exempt
def delete_task(request):
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task = data.get('task')
            logger.info(task)
            if task:
                task = Task.objects.get(id=task.get('id'))
                task.delete()
                return JsonResponse({'status': 'success', 'message': 'Task deleted'})
            return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def update_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Parsed data:", data)  # Log parsed data to inspect the content
            task_index= data.get('index')
            status = data.get('status')
            
            if task_index and status is not None:
                try:
                    task = Task.objects.get(id=task_index)
                    task.status = status
                    task.save()
                    return JsonResponse({'status': 'success', 'message': 'Task updated'})
                except Task.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
            
            return JsonResponse({'status': 'error', 'message': 'Invalid task or status'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
