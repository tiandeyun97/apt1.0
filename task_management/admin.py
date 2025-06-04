from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import admin
from .models import Task, TaskStatus, Project
from .permissions import TaskPermission
from django.http import JsonResponse
from organize.models import User  # 修正导入，使用正确的User模型

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # 其他配置...
    
    # 设置自定义模板
    change_list_template = 'admin/task_management/task/task_list.html'  # 任务列表
    add_form_template = 'admin/task_management/task/task_form.html'  # 新增任务表单
    change_form_template = 'admin/task_management/task/task_form.html'  # 编辑任务表单
    
    # 允许筛选的字段
    list_filter = ['name', 'advert_name', 'project', 'status', 'optimizer']
    search_fields = ['name', 'advert_name']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import_tasks/', self.admin_site.admin_view(self.import_tasks_view), name='import_tasks'),
            path('get_task_detail/', self.admin_site.admin_view(self.get_task_detail), name='get_task_detail'),
        ]
        return custom_urls + urls
    
    def get_queryset(self, request):
        """根据用户角色过滤任务数据"""
        queryset = super().get_queryset(request)
        return TaskPermission.filter_tasks_by_role(queryset, request.user)
    
    def import_tasks_view(self, request):
        """任务导入视图"""
        # 导入处理逻辑...
        context = {
            'title': '批量导入任务',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/task_management/task/task_import.html', context)
    
    def get_task_detail(self, request):
        """获取任务详情"""
        task_id = request.GET.get('task_id')
        if task_id:
            try:
                # 获取任务对象
                task = Task.objects.get(pk=task_id)
                
                # 使用TaskPermission检查权限
                permitted_tasks = TaskPermission.filter_tasks_by_role(Task.objects.filter(pk=task_id), request.user)
                if not permitted_tasks.exists():
                    return JsonResponse({'success': False, 'message': '您没有权限查看此任务'})
                
                # 获取优化师列表
                optimizers = [{"id": optimizer.id, "username": optimizer.username} for optimizer in task.optimizer.all()]
                
                data = {
                    'success': True,
                    'id': str(task.id),
                    'name': task.name,
                    'advert_name': task.advert_name,
                    'project': {
                        'id': task.project.ProjectID,
                        'name': task.project.ProjectName,
                        'media_channel': task.project.MediaChannelID.MediaChannelName if task.project.MediaChannelID else '-',
                        'task_type': task.project.TaskTypeID.TaskTypeName if task.project.TaskTypeID else '-',
                        'daily_report_url': task.project.DailyReportURL or '-',
                        'kpi': task.project.KPI or '-',
                        'manager': task.project.ManagerID.username if task.project.ManagerID else '-',
                        'timezone': task.project.TimeZone or '-'
                    },
                    'product_info': task.product_info or '',
                    'status': {
                        'id': task.status.TaskStatusID,
                        'name': task.status.TaskStatusName
                    },
                    'backend': task.backend or '',
                    'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'start_date': task.start_date.strftime('%Y-%m-%d'),
                    'end_date': task.end_date.strftime('%Y-%m-%d') if task.end_date else '-',
                    'notes': task.notes or '',
                    'pixel': task.pixel or '',
                    'publish_url': task.publish_url or '',
                    'optimizers': optimizers
                }
                return JsonResponse(data)
            except Task.DoesNotExist:
                return JsonResponse({'success': False, 'message': '任务不存在'})
        else:
            return JsonResponse({'success': False, 'message': '未提供任务ID'})
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # 获取基础查询集
        queryset = self.model.objects.all()
        
        # 只对公司数据进行过滤
        if request.user.company:
            queryset = queryset.filter(company=request.user.company)
        
        # 应用权限过滤
        filtered_queryset = TaskPermission.filter_tasks_by_role(queryset, request.user)
        
        # 处理任务名称搜索
        name_query = request.GET.get('name')
        if name_query:
            filtered_queryset = filtered_queryset.filter(name__icontains=name_query)
            
        # 处理任务状态搜索
        status_query = request.GET.get('status')
        if status_query:
            filtered_queryset = filtered_queryset.filter(status__TaskStatusID=status_query)
            
        # 处理项目名称模糊搜索
        project_name_query = request.GET.get('project_name')
        if project_name_query:
            filtered_queryset = filtered_queryset.filter(project__ProjectName__icontains=project_name_query)
        # 处理项目ID精确搜索（保持向后兼容）    
        elif project_query := request.GET.get('project'):
            filtered_queryset = filtered_queryset.filter(project__ProjectID=project_query)
            
        # 处理优化师搜索
        optimizer_query = request.GET.get('optimizer')
        if optimizer_query:
            # 多选情况下，会得到逗号分隔的ID字符串
            optimizer_ids = optimizer_query.split(',')
            if len(optimizer_ids) > 0 and optimizer_ids[0]:  # 确保有有效的ID
                filtered_queryset = filtered_queryset.filter(optimizer__id__in=optimizer_ids).distinct()
        
        # 应用排序
        filtered_queryset = filtered_queryset.distinct().order_by('-created_at')
        
        # 实现分页
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        
        # 获取用户设置的每页记录数，默认为20条
        per_page = request.GET.get('per_page', 20)
        try:
            per_page = int(per_page)
            # 限制可选择的每页记录数
            if per_page not in [10, 20, 50, 100]:
                per_page = 20
        except (ValueError, TypeError):
            per_page = 20
            
        paginator = Paginator(filtered_queryset, per_page)  # 使用用户自定义的每页显示条数
        page = request.GET.get('page')
        
        try:
            tasks = paginator.page(page)
        except PageNotAnInteger:
            # 如果page不是整数，显示第一页
            tasks = paginator.page(1)
        except EmptyPage:
            # 如果page超出范围，显示最后一页
            tasks = paginator.page(paginator.num_pages)
        
        # 将分页结果传递给模板
        extra_context['tasks'] = tasks
        extra_context['paginator'] = paginator
        extra_context['page_obj'] = tasks
        extra_context['is_paginated'] = True
        extra_context['per_page'] = per_page  # 传递当前每页显示条数到模板
        
        # 获取当前用户有权限看到的任务状态
        visible_status_ids = filtered_queryset.values_list('status', flat=True).distinct()
        extra_context['statuses'] = TaskStatus.objects.filter(TaskStatusID__in=visible_status_ids)
        
        # 获取当前用户有权限看到的项目列表
        visible_project_ids = filtered_queryset.values_list('project', flat=True).distinct()
        if request.user.company:
            extra_context['projects'] = Project.objects.filter(
                ProjectID__in=visible_project_ids,
                CompanyID=request.user.company
            ).order_by('ProjectName')
        else:
            extra_context['projects'] = Project.objects.none()
            
        # 获取当前用户有权限看到的优化师列表
        visible_optimizer_ids = filtered_queryset.values_list('optimizer', flat=True).distinct()
        if request.user.company:
            extra_context['optimizers'] = User.objects.filter(
                id__in=visible_optimizer_ids,
                company=request.user.company,
                groups__name__in=['优化师', '部门主管', '小组长']
            ).order_by('username')
        else:
            extra_context['optimizers'] = User.objects.none()
        
        # 使用自定义模板渲染
        return TemplateResponse(
            request,
            self.change_list_template,
            context=extra_context
        )
