from django.urls import path
from . import views

app_name = 'reconciliation'

urlpatterns = [
    # 首页 - 重定向到等待对账
    path('', views.index, name='index'),
    
    # 对账列表
    path('waiting/', views.waiting_list, name='waiting_list'),
    path('exception/', views.exception_list, name='exception_list'),
    path('completed/', views.completed_list, name='completed_list'),
    
    # 对账详情和操作
    path('record/<uuid:record_id>/', views.record_detail, name='record_detail'),
    path('record/<uuid:record_id>/update/', views.update_fb_consumption, name='update_fb_consumption'),
    path('record/<uuid:record_id>/confirm/', views.manual_confirm, name='manual_confirm'),
    path('record/<uuid:record_id>/upload/', views.upload_attachment, name='upload_attachment'),
    
    # 数据导出
    path('export/', views.export_data, name='export_data'),
    
    # AJAX接口
    path('api/record/<uuid:record_id>/history/', views.record_history_api, name='record_history_api'),
    path('api/record/<uuid:record_id>/attachments/', views.record_attachments_api, name='record_attachments_api'),
    path('api/batch-update/', views.batch_update_fb_consumption, name='batch_update_fb_consumption'),
    path('api/batch-confirm/', views.batch_manual_confirm, name='batch_manual_confirm'),
] 