from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

class CustomAdminSite(AdminSite):
    """自定义管理站点，重定向首页到任务管理页面"""
    
    def index(self, request, extra_context=None):
        """重写index视图，将管理员重定向到任务管理页面"""
        # 检查用户是否已登录
        if request.user.is_authenticated:
            return redirect('admin:task_management_task_changelist')
        # 如果未登录则使用默认首页（会重定向到登录页）
        return super().index(request, extra_context)

# 创建自定义管理站点实例
custom_admin_site = CustomAdminSite(name='custom_admin')

# 注册权限相关模型
from django.contrib import admin
admin.site.register(Permission)
admin.site.register(ContentType) 