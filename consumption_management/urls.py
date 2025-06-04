from django.urls import path
from . import views

app_name = 'consumption_stats'

urlpatterns = [
    path('task/<uuid:task_id>/add/', views.add_task_consumption, name='add_task_consumption'),
    path('task/<uuid:task_id>/list/', views.TaskConsumptionListView.as_view(), name='task_consumption_list_by_task'),
    path('task/<uuid:task_id>/delete/<uuid:consumption_id>/', views.delete_task_consumption, name='delete_task_consumption'),
    path('task/<uuid:task_id>/edit/<uuid:consumption_id>/', views.edit_task_consumption, name='edit_task_consumption'),
    path('task/<uuid:task_id>/get-consumption/<uuid:consumption_id>/', views.get_task_consumption, name='get_task_consumption'),
    path('task/<uuid:task_id>/get-optimizers-count/', views.get_task_optimizers_count, name='get_task_optimizers_count'),
    path('consumption/<uuid:consumption_id>/update-return-flow/', views.update_return_flow, name='update_return_flow'),
    path('records/', views.consumption_records_list, name='consumption_records_list'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('import-template/', views.download_import_template, name='download_import_template'),
    path('import-consumptions/', views.import_consumptions, name='import_consumptions'),
    path('confirm-import/', views.confirm_import, name='confirm_import'),
    path('project-view-data/', views.project_view_data, name='project_view_data'),
    path('search-projects/', views.search_projects, name='search_projects'),
    path('search-tasks/', views.search_tasks, name='search_tasks'),
] 