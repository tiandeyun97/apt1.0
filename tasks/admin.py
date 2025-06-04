from django.contrib import admin
from django.forms import ModelForm
from django.db.models import Q
from django.forms.widgets import Select
from django.http import JsonResponse
from django.urls import path
from .models import MediaChannel, TaskType, TaskStatus, Project
from organize.models import User, Company, Department
from .forms import ProjectForm, MediaChannelForm, TaskTypeForm, TaskStatusForm

# Admin视图类
class AdminMediaChannelAdmin(admin.ModelAdmin):
    """媒体渠道后台管理视图"""
    list_display = ['MediaChannelName', 'CompanyID', 'Description']
    list_filter = ['CompanyID']
    search_fields = ['MediaChannelName']
    exclude = ['CompanyID']  # 从表单中排除，避免用户手动设置
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(CompanyID=request.user.company)

    def save_model(self, request, obj, form, change):
        # 无论是否是修改操作，都确保设置公司ID
        obj.CompanyID = request.user.company
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser and db_field.name == "CompanyID":
            kwargs["queryset"] = Company.objects.filter(pk=request.user.company.pk)
            kwargs["initial"] = request.user.company
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AdminTaskTypeAdmin(admin.ModelAdmin):
    """任务类型后台管理视图"""
    list_display = ['TaskTypeName', 'CompanyID', 'Description']
    list_filter = ['CompanyID']
    search_fields = ['TaskTypeName']
    exclude = ['CompanyID']  # 从表单中排除，避免用户手动设置
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(CompanyID=request.user.company)

    def save_model(self, request, obj, form, change):
        # 无论是否是修改操作，都确保设置公司ID
        obj.CompanyID = request.user.company
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser and db_field.name == "CompanyID":
            kwargs["queryset"] = Company.objects.filter(pk=request.user.company.pk)
            kwargs["initial"] = request.user.company
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AdminTaskStatusAdmin(admin.ModelAdmin):
    """任务状态后台管理视图"""
    list_display = ['TaskStatusName', 'CompanyID', 'Description']
    list_filter = ['CompanyID']
    search_fields = ['TaskStatusName']
    exclude = ['CompanyID']  # 从表单中排除，避免用户手动设置
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(CompanyID=request.user.company)

    def save_model(self, request, obj, form, change):
        # 无论是否是修改操作，都确保设置公司ID
        obj.CompanyID = request.user.company
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser and db_field.name == "CompanyID":
            kwargs["queryset"] = Company.objects.filter(pk=request.user.company.pk)
            kwargs["initial"] = request.user.company
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AdminProjectAdmin(admin.ModelAdmin):
    """项目后台管理视图"""
    list_display = ['ProjectID', 'ProjectName', 'CompanyID', 'ManagerID', 'TaskTypeID', 'MediaChannelID', 'StartDate', 'EndDate', 'Status2']
    list_display_links = ['ProjectName']  # 设置点击项目名称进入编辑页面
    list_filter = ['CompanyID', 'Status2', 'TaskTypeID', 'MediaChannelID', 'StartDate', 'EndDate']
    search_fields = ['ProjectName']
    form = ProjectForm
    change_list_template = 'tasks/project_list.html'  # 自定义项目列表模板
    list_per_page = 10  # 默认每页显示10条记录
    
    def get_list_per_page(self, request):
        """根据请求参数动态设置每页显示记录数"""
        list_per_page = request.GET.get('list_per_page')
        try:
            list_per_page = int(list_per_page)
            # 限制每页显示记录数在合理范围内
            if list_per_page in [10, 20, 50, 100]:
                return list_per_page
        except (ValueError, TypeError):
            pass
        return self.list_per_page
    
    def get_changelist_instance(self, request):
        """确保模板有正确的上下文"""
        # 设置每页显示记录数
        self.list_per_page = self.get_list_per_page(request)
        
        cl = super().get_changelist_instance(request)
        
        # 添加项目统计数据
        queryset = self.get_queryset(request)
        cl.total_projects = queryset.count()
        cl.active_projects = queryset.filter(Status='进行中').count()
        cl.paused_projects = queryset.filter(Status='已暂停').count()
        cl.completed_projects = queryset.filter(Status='已完成').count()
        
        # 添加筛选数据
        cl.task_types = TaskType.objects.filter(CompanyID=request.user.company)
        cl.media_channels = MediaChannel.objects.filter(CompanyID=request.user.company)
        
        # 获取选中的筛选值
        cl.selected_task_type_id = request.GET.get('task_type_id', '')
        cl.selected_channel_id = request.GET.get('media_channel_id', '')
        cl.selected_status = request.GET.get('status', '')
        
        # 处理分页参数，但不从params中删除p参数，这样可以在表单中使用
        cl.params = dict(request.GET.items())
        # 保留所有查询参数，以便在表单页面返回时仍然能够回到原来的页面
        # 保存搜索关键词
        cl.query = cl.params.get('q', '')
        
        # 将每页显示记录数传递给模板
        cl.list_per_page = self.list_per_page
        
        # 确保页码是整数
        try:
            cl.page_num = int(request.GET.get('p', 1))
        except (ValueError, TypeError):
            cl.page_num = 1
        
        # 确保页码在有效范围内
        if cl.page_num < 1:
            cl.page_num = 1
        elif cl.paginator and cl.page_num > cl.paginator.num_pages:
            cl.page_num = cl.paginator.num_pages
        
        return cl
    
    def get_form(self, request, obj=None, change=False, **kwargs):
        # 先获取表单类
        FormClass = super().get_form(request, obj, **kwargs)
        
        # 创建一个新的表单类，继承自原来的表单类，并添加request属性
        class RequestFormClass(FormClass):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.request = request
        
        if obj:  # 编辑现有对象时
            # 格式化日期字段
            if obj.StartDate:
                FormClass.base_fields['StartDate'].initial = obj.StartDate.strftime('%Y-%m-%d')
            if obj.EndDate:
                FormClass.base_fields['EndDate'].initial = obj.EndDate.strftime('%Y-%m-%d')
                
        # 设置日期字段的widget属性
        FormClass.base_fields['StartDate'].widget.attrs.update({
            'class': 'form-control',
            'type': 'date'
        })
        FormClass.base_fields['EndDate'].widget.attrs.update({
            'class': 'form-control',
            'type': 'date'
        })
        
        return RequestFormClass

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(CompanyID=request.user.company)

    def save_model(self, request, obj, form, change):
        if not change:  # 如果是新建
            obj.CompanyID = request.user.company
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "CompanyID":
                kwargs["queryset"] = Company.objects.filter(pk=request.user.company.pk)
                kwargs["initial"] = request.user.company
            elif db_field.name == "ManagerID":
                # 只显示用户角色组为运营的用户
                kwargs["queryset"] = User.objects.filter(
                    company=request.user.company,
                    groups__name='运营'
                ).distinct()
            elif db_field.name in ["TaskTypeID", "MediaChannelID"]:
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    CompanyID=request.user.company
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# 注册模型到admin后台
admin.site.register(MediaChannel, AdminMediaChannelAdmin)
admin.site.register(TaskType, AdminTaskTypeAdmin)
admin.site.register(TaskStatus, AdminTaskStatusAdmin)
admin.site.register(Project, AdminProjectAdmin)


