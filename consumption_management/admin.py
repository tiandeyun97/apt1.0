from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from .models import TaskConsumption, TaskConsumptionMonitor
from .permissions import filter_queryset_by_role
from django.http import JsonResponse

@admin.register(TaskConsumption)
class TaskConsumptionAdmin(admin.ModelAdmin):
    list_display = ['task', 'date', 'daily_consumption', 'return_flow', 'actual_consumption', 'registrations', 'first_deposits']
    #list_filter = ['task__project', 'date']
    #search_fields = ['task__name']
    #date_hierarchy = 'date'
    
    # 设置自定义模板
    change_list_template = 'consumption_stats/consumption_records_list.html'  # 消耗记录列表
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('consumption_records/', self.admin_site.admin_view(self.consumption_records_view), name='consumption_records'),
        ]
        return custom_urls + urls
    
    def get_queryset(self, request):
        """根据用户角色过滤消耗记录数据"""
        queryset = super().get_queryset(request)
        return filter_queryset_by_role(queryset, request.user, "taskconsumption")
    
    def consumption_records_view(self, request):
        """消耗记录列表视图"""
        # 这里直接调用自定义视图函数
        from .views import consumption_records_list
        return consumption_records_list(request)
    
    def changelist_view(self, request, extra_context=None):
        # 如果是从Django admin访问，则重定向到自定义视图
        if not request.path.endswith('/consumption_records/'):
            from django.shortcuts import redirect
            return redirect('admin:consumption_records')
        
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(TaskConsumptionMonitor)
class TaskConsumptionMonitorAdmin(admin.ModelAdmin):
    """消耗监控管理"""
    change_list_template = 'consumption_stats/task_consumption_monitor.html'  # 使用监控面板模板
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.consumption_monitor_view), name='consumption_monitor'),
        ]
        return custom_urls + urls
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
        
    # 禁用显示任何数据列表，直接使用自定义视图
    def get_queryset(self, request):
        # 返回空查询集，因为我们只使用自定义视图
        return TaskConsumptionMonitor.objects.none()
    
    def consumption_monitor_view(self, request):
        """任务消耗记录监控视图"""
        # 调用监控视图函数
        from .views import task_consumption_monitor
        return task_consumption_monitor(request)
