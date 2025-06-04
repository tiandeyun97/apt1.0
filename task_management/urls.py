from django.urls import path
from . import views

app_name = 'task_management'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),  # 任务列表作为默认页面
    path('create/', views.TaskCreateView.as_view(), name='task_create'),
    path('delete/<uuid:pk>/', views.TaskDeleteView.as_view(), name='task_delete'),  # 添加删除URL
    path('get-project-info/', views.get_project_info, name='get_project_info'),
    path('get-task-detail/', views.get_task_detail, name='get_task_detail'),
    path('import/', views.import_tasks, name='import_tasks'),  # 添加批量导入任务URL
    path('task-import/', views.import_tasks, name='task_import'),  # 添加兼容的URL路径
    path('download-template/', views.download_task_template, name='download_template'),  # 添加下载模板URL
    path('export-excel/', views.export_tasks_excel, name='export_tasks_excel'),  # 添加导出Excel URL
    path('update-status/', views.update_task_status, name='update_task_status'),  # 添加更新任务状态的API
    path('update-end-date/', views.update_task_end_date, name='update_task_end_date'),  # 添加更新任务结束日期的API
]