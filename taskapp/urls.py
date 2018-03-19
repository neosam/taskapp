from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('logout', views.logout, name='logout'),
    path('complete/<int:task_id>', views.complete, name='complete'),
    path('edit-task/<int:task_id>', views.edit_task, name='edit_task'),
    path('new-task/<int:company_id>', views.new_task, name='new_task'),
    path('new-user-task/<int:user_setup_id>', views.new_user_task, name='new_user_task'),
    path('user-setup-details/<int:user_setup_id>', views.user_setup_details, name='user_setup_details'),
    path('revert-history-item/<int:history_id>', views.revert_history_item, name='revert_history_item'),
    path('mod-score/<int:user_setup_id>', views.mod_score, name='mod_score'),
    path('json-data/<int:user_id>', views.json_data, name='json_data'),
    path('json-verify-login', views.json_login, name="json_login"),
    

]