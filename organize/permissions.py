from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class BasePermissionMixin(UserPassesTestMixin):
    """基础权限Mixin
    
    提供通用的权限检查功能
    """
    def test_func(self):
        if self.request.user.is_superuser:
            return True
            
        required_perm = self.get_required_permission()
        return self.request.user.has_perm(required_perm)
    
    def get_required_permission(self):
        """获取所需权限
        
        子类必须实现此方法以返回所需的权限字符串
        """
        raise NotImplementedError
        
    def handle_no_permission(self):
        raise PermissionDenied("您没有执行此操作的权限。")

class CompanyPermissionMixin(BasePermissionMixin):
    """公司相关权限Mixin"""
    def get_required_permission(self):
        action = getattr(self, 'action', 'view')
        return f'organize.{action}_company'
        
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(pk=self.request.user.company.pk)
        return qs

class DepartmentPermissionMixin(BasePermissionMixin):
    """部门相关权限Mixin"""
    def get_required_permission(self):
        action = getattr(self, 'action', 'view')
        return f'organize.{action}_department'
        
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(company=self.request.user.company)
        return qs

class UserPermissionMixin(BasePermissionMixin):
    """用户相关权限Mixin"""
    def get_required_permission(self):
        action = getattr(self, 'action', 'view')
        return f'organize.{action}_user'
        
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(company=self.request.user.company)
        return qs

# 权限常量定义
COMPANY_PERMISSIONS = [
    ('view_company', 'Can view company (浏览公司)'),
    ('add_company', 'Can add company (新建公司)'),
    ('change_company', 'Can change company (编辑公司)'),
    ('delete_company', 'Can delete company (删除公司)'),
]

DEPARTMENT_PERMISSIONS = [
    ('view_department', 'Can view department (浏览部门)'),
    ('add_department', 'Can add department (新建部门)'),
    ('change_department', 'Can change department (编辑部门)'),
    ('delete_department', 'Can delete department (删除部门)'),
]

USER_PERMISSIONS = [
    ('view_user', 'Can view user (浏览用户)'),
    ('add_user', 'Can add user (新建用户)'),
    ('change_user', 'Can change user (编辑用户)'),
    ('delete_user', 'Can delete user (删除用户)'),
] 