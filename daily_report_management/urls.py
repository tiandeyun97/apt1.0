from django.urls import path
from . import views

app_name = 'daily_report_management'

urlpatterns = [
    path('list/', views.daily_report_list, name='daily_report_list'),
    path('create/', views.create_daily_report, name='create_daily_report'),
    path('delete/<int:report_id>/', views.delete_daily_report, name='delete_daily_report'),
    path('dailyreport/', views.daily_report_page, name='daily_report_page'),
] 