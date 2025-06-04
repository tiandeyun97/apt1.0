from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from organize.permissions import BasePermissionMixin

class ProjectPermissionMixin(BasePermissionMixin):
    """项目相关权限Mixin"""
    def get_required_permission(self):
        action = getattr(self, 'action', 'view')
        return f'tasks.{action}_project'
        
    def get_queryset(self):
        qs = super().get_queryset()
        # 非超级管理员只能看到自己公司的项目
        if not self.request.user.is_superuser:
            qs = qs.filter(CompanyID=self.request.user.company)
        return qs

class MediaChannelPermissionMixin(BasePermissionMixin):
    """媒体渠道相关权限Mixin"""
    def get_required_permission(self):
        action = getattr(self, 'action', 'view')
        return f'tasks.{action}_mediachannel'
        
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(CompanyID=self.request.user.company)
        return qs

class TaskTypePermissionMixin(BasePermissionMixin):
    """任务类型相关权限Mixin"""
    def get_required_permission(self):
        action = getattr(self, 'action', 'view')
        return f'tasks.{action}_tasktype'
        
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(CompanyID=self.request.user.company)
        return qs

class TaskStatusPermissionMixin(BasePermissionMixin):
    """任务状态相关权限Mixin"""
    def get_required_permission(self):
        action = getattr(self, 'action', 'view')
        return f'tasks.{action}_taskstatus'
        
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(CompanyID=self.request.user.company)
        return qs

class ProjectTaskPermissionMixin(BasePermissionMixin):
    """项目任务相关权限Mixin"""
    def get_required_permission(self):
        action = getattr(self, 'action', 'view')
        return f'tasks.{action}_projecttask'
        
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser:
            return qs
            
        # 过滤用户所在公司的项目任务
        qs = qs.filter(project__company=user.company)
        
        # 如果用户有查看所有项目任务的权限
        if user.has_perm('tasks.view_all_project_tasks'):
            return qs
            
        # 如果用户有查看部门项目任务的权限
        if user.has_perm('tasks.view_department_project_tasks'):
            departments = user.departments.all()
            return qs.filter(
                Q(project__department__in=departments) |
                Q(project__parent_department__in=departments)
            )
            
        # 普通用户只能查看分配给自己的项目任务
        return qs.filter(
            Q(project__manager=user) |
            Q(project__members=user)
        ).distinct()

# 权限常量定义
PROJECT_PERMISSIONS = [
    # 基础操作权限
    ('view_project', 'Can view project (浏览项目)'),
    ('add_project', 'Can add project (新建项目)'),
    ('change_project', 'Can change project (编辑项目)'),
    ('delete_project', 'Can delete project (删除项目)'),
]

TASK_PERMISSIONS = [
    ('view_task', 'Can view task (浏览任务)'),
    ('add_task', 'Can add task (新建任务)'),
    ('change_task', 'Can change task (编辑任务)'),
    ('delete_task', 'Can delete task (删除任务)'),
    ('view_my_tasks', 'Can view my tasks (查看我的任务)'),
    ('view_consumption_record', 'Can view consumption record (查看消耗记录)'),
]

MEDIA_CHANNEL_PERMISSIONS = [
    # 基础操作权限
    ('view_mediachannel', 'Can view media channel (浏览媒体渠道)'),
    ('add_mediachannel', 'Can add media channel (新建媒体渠道)'),
    ('change_mediachannel', 'Can change media channel (编辑媒体渠道)'),
    ('delete_mediachannel', 'Can delete media channel (删除媒体渠道)'),
]

TASK_TYPE_PERMISSIONS = [
    # 系统配置权限
    ('view_tasktype', 'Can view task type (浏览任务类型)'),
    ('add_tasktype', 'Can add task type (新建任务类型)'),
    ('change_tasktype', 'Can change task type (编辑任务类型)'),
    ('delete_tasktype', 'Can delete task type (删除任务类型)'),
]

TASK_STATUS_PERMISSIONS = [
    # 系统配置权限
    ('view_taskstatus', 'Can view task status (浏览任务状态)'),
    ('add_taskstatus', 'Can add task status (新建任务状态)'),
    ('change_taskstatus', 'Can change task status (编辑任务状态)'),
    ('delete_taskstatus', 'Can delete task status (删除任务状态)'),
] 