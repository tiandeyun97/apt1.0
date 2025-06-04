from django.urls import path
from . import views

app_name = 'pixel_management'

urlpatterns = [
    path('', views.pixel_list, name='pixel_list'),
    path('<int:pk>/', views.pixel_detail, name='pixel_detail'),
    path('create/', views.pixel_create, name='pixel_create'),
    path('<int:pk>/edit/', views.pixel_edit, name='pixel_edit'),
    path('<int:pk>/toggle-authorization/', views.toggle_authorization, name='toggle_authorization'),
    path('<int:pk>/delete/', views.pixel_delete, name='pixel_delete'),
    path('check-task-availability/', views.check_task_availability, name='check_task_availability'),
]
