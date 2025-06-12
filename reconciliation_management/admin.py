from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from .models import ReconciliationRecord, ReconciliationHistory, ReconciliationAttachment
from . import views
from django.shortcuts import redirect

class ReconciliationHistoryInline(admin.TabularInline):
    model = ReconciliationHistory
    extra = 0
    readonly_fields = ('action', 'old_status', 'new_status', 'old_fb_consumption', 'new_fb_consumption', 'difference', 'note', 'operated_by', 'operated_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

class ReconciliationAttachmentInline(admin.TabularInline):
    model = ReconciliationAttachment
    extra = 0
    readonly_fields = ('file', 'file_name', 'file_size', 'uploaded_by', 'uploaded_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ReconciliationRecord)
class ReconciliationRecordAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'project', 'task', 'actual_consumption', 'fb_consumption', 'difference', 'difference_percentage', 'status', 'is_manually_confirmed', 'created_at')
    list_filter = ('year', 'month', 'status', 'is_manually_confirmed', 'project')
    search_fields = ('project__ProjectName', 'task__name')
    readonly_fields = ('year', 'month', 'project', 'task', 'actual_consumption', 'difference', 'difference_percentage', 'created_at', 'updated_at')
    
    # 设置默认列表视图模板为waiting_list
    change_list_template = 'reconciliation_management/waiting_list.html'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('year', 'month', 'project', 'task')
        }),
        ('消耗信息', {
            'fields': ('actual_consumption', 'fb_consumption', 'difference', 'difference_percentage')
        }),
        ('状态信息', {
            'fields': ('status', 'is_manually_confirmed', 'confirmed_by', 'confirmed_at', 'note')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [ReconciliationHistoryInline, ReconciliationAttachmentInline]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('waiting/', self.admin_site.admin_view(views.waiting_list), name='reconciliation_waiting_list'),
            path('exception/', self.admin_site.admin_view(views.exception_list), name='reconciliation_exception_list'),
            path('completed/', self.admin_site.admin_view(views.completed_list), name='reconciliation_completed_list'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """自定义列表视图"""
        # 检查是否有查询参数，如果没有，重定向到waiting_list视图
        if not request.GET:
            return redirect('/admin/reconciliation_management/reconciliationrecord/waiting/')
            
        if extra_context is None:
            extra_context = {}
        return super().changelist_view(request, extra_context)

@admin.register(ReconciliationHistory)
class ReconciliationHistoryAdmin(admin.ModelAdmin):
    list_display = ('reconciliation', 'action', 'old_status', 'new_status', 'operated_by', 'operated_at')
    list_filter = ('action', 'new_status', 'operated_at')
    search_fields = ('reconciliation__task__name', 'note', 'operated_by__username')
    readonly_fields = ('reconciliation', 'action', 'old_status', 'new_status', 'old_fb_consumption', 'new_fb_consumption', 'difference', 'note', 'operated_by', 'operated_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(ReconciliationAttachment)
class ReconciliationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('reconciliation', 'file_name', 'file_size', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('reconciliation__task__name', 'file_name', 'uploaded_by__username')
    readonly_fields = ('reconciliation', 'file', 'file_name', 'file_size', 'uploaded_by', 'uploaded_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
