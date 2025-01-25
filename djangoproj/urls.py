from django.contrib import admin
from django.urls import path
from .import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('create', views.create_task, name='index'),
    path('get_tasks', views.get_tasks, name='index'),
    path('delete_task', views.delete_task, name='delete_task'),
    path('update_task', views.update_task, name='update_task'),
    #path('sort_task', views.sort_task, name='sort_task'),
]
