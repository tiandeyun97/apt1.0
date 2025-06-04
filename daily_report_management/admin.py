from django.contrib import admin
from .models import DailyReport
from django.utils.html import format_html
from task_management.permissions import TaskPermission
from task_management.models import Task
from django.db.models import Q

# Register your models here.
@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    # 使用自定义模板
    change_list_template = 'daily_report_management/daily_report_list.html'
    
    # 只保留必要的字段
    list_display = ('date', 'channel_name', 'optimizers', 'consumption', 'registrations', 'first_deposits',
                   'registration_cost', 'first_deposit_cost', 'budget', 'kpi',
                    'daily_recharge_rate', 'retention_day2', 'retention_day3', 'retention_day4',
                   'retention_day5', 'retention_day7', 'budget_description')
    list_per_page = 20
    list_display_links = ('date', 'channel_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'registration_cost', 'first_deposit_cost', 'optimizers')
    search_fields = ('channel_name',)
    list_filter = ('date',)
    fieldsets = (
        ('基本信息', {
            'fields': ('date', 'channel_name', 'budget_description')
        }),
        ('数据指标', {
            'fields': ('consumption', 'registrations', 'first_deposits', 'budget', 'kpi')
        }),
        ('留存指标', {
            'fields': ('daily_recharge_rate', 'retention_day2', 'retention_day3', 
                      'retention_day4', 'retention_day5', 'retention_day7'),
        }),
    )
    
    def get_queryset(self, request):
        """按时间降序排列数据，并根据用户权限过滤数据"""
        queryset = super().get_queryset(request)
        
        # 基础排序
        queryset = queryset.order_by('-date', 'channel_name')
        
        # 如果用户没有登录，直接返回空查询集
        if not request.user.is_authenticated:
            return queryset.none()
            
        # 如果是超级用户，返回所有数据
        if request.user.is_superuser:
            return queryset
        
        # 使用TaskPermission获取用户可见的任务
        visible_tasks = TaskPermission.filter_tasks_by_role(Task.objects.all(), request.user)
        
        # 从可见任务中获取相关的channel_name
        channel_names = []
        for task in visible_tasks:
            if task.name:
                channel_names.append(task.name)
            if task.advert_name:
                channel_names.append(task.advert_name)
        
        # 如果没有找到任何可见的渠道，返回空查询集
        if not channel_names:
            return queryset.none()
            
        # 构建查询条件，查找channel_name包含在可见任务列表中的日报
        filter_condition = Q()
        for name in channel_names:
            filter_condition |= Q(channel_name__icontains=name)
            
        return queryset.filter(filter_condition).distinct()
    
    def has_delete_permission(self, request, obj=None):
        """检查是否有删除权限"""
        # 只有超级用户有删除权限
        return request.user.is_superuser

    def get_search_results(self, request, queryset, search_term):
        """重写搜索结果方法，确保只能搜索用户有权限的渠道数据"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # 如果没有搜索词，直接返回原始查询集
        if not search_term:
            return queryset, use_distinct
            
        # 如果用户是超级用户，直接返回搜索结果
        if request.user.is_superuser:
            return queryset, use_distinct
            
        # 获取用户可见的渠道名称
        visible_tasks = TaskPermission.filter_tasks_by_role(Task.objects.all(), request.user)
        
        # 从可见任务中获取相关的channel_name
        channel_names = []
        for task in visible_tasks:
            if task.name:
                channel_names.append(task.name)
            if task.advert_name:
                channel_names.append(task.advert_name)
                
        # 构建查询条件，查找channel_name中包含搜索词且在用户可见渠道列表中的记录
        filter_condition = Q()
        for name in channel_names:
            if search_term.lower() in name.lower():
                filter_condition |= Q(channel_name__icontains=name)
                
        # 如果没有找到匹配的渠道，返回空查询集
        if not filter_condition:
            return queryset.none(), use_distinct
            
        return queryset.filter(filter_condition).distinct(), True

    def channel_name_display(self, obj):
        """自定义渠道名称显示"""
        return format_html('<div class="channel-name-container" title="{}">{}</div>', 
                          obj.channel_name, obj.channel_name)
    
    channel_name_display.short_description = '渠道名称'
    channel_name_display.admin_order_field = 'channel_name'
