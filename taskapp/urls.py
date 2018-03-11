from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('complete/<int:task_id>', views.complete, name='complete'),
    path('edit-task/<int:task_id>', views.edit_task, name='edit_task'),
]