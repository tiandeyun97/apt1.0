from django.urls import path
from . import views
from .api import project_detail_api, get_optimizers

app_name = 'tasks'

urlpatterns = [
    # API URLs
    path('api/project/<int:project_id>/', project_detail_api, name='project_detail_api'),
    path('api/optimizers/', get_optimizers, name='get_optimizers'),
    
    # 项目URLs
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    
    # 媒体渠道URLs
    path('media-channels/', views.MediaChannelListView.as_view(), name='media_channel_list'),
    path('media-channels/<int:pk>/', views.MediaChannelDetailView.as_view(), name='media_channel_detail'),
    path('media-channels/create/', views.MediaChannelCreateView.as_view(), name='media_channel_create'),
    path('media-channels/<int:pk>/update/', views.MediaChannelUpdateView.as_view(), name='media_channel_update'),
    path('media-channels/<int:pk>/delete/', views.MediaChannelDeleteView.as_view(), name='media_channel_delete'),
    
    # 任务类型URLs
    path('task-types/', views.TaskTypeListView.as_view(), name='task_type_list'),
    path('task-types/<int:pk>/', views.TaskTypeDetailView.as_view(), name='task_type_detail'),
    path('task-types/create/', views.TaskTypeCreateView.as_view(), name='task_type_create'),
    path('task-types/<int:pk>/update/', views.TaskTypeUpdateView.as_view(), name='task_type_update'),
    path('task-types/<int:pk>/delete/', views.TaskTypeDeleteView.as_view(), name='task_type_delete'),
    
    # 任务状态URLs
    path('task-statuses/', views.TaskStatusListView.as_view(), name='task_status_list'),
    path('task-statuses/<int:pk>/', views.TaskStatusDetailView.as_view(), name='task_status_detail'),
    path('task-statuses/create/', views.TaskStatusCreateView.as_view(), name='task_status_create'),
    path('task-statuses/<int:pk>/update/', views.TaskStatusUpdateView.as_view(), name='task_status_update'),
    path('task-statuses/<int:pk>/delete/', views.TaskStatusDeleteView.as_view(), name='task_status_delete'),
] 