from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('complete/<int:task_id>', views.complete, name='complete'),
    path('edit-task/<int:task_id>', views.edit_task, name='edit_task'),
    path('new-task/<int:company_id>', views.new_task, name='new_task'),
    path('user-setup-details/<int:user_setup_id>', views.user_setup_details, name='user_setup_details'),
    

]