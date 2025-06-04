"""
URL configuration for ad_manplat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf import settings

# 自定义admin站点设置
admin.site.site_header = '广告投放管理平台'
admin.site.site_title = '广告管理系统'
admin.site.index_title = '后台管理'
admin.autodiscover()

# Admin登录退出视图
class AdminLoginView(auth_views.LoginView):
    template_name = 'admin/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': '广告管理后台',
            'site_title': '',
            'site_header': ''
        })
        return context

    def get_success_url(self):
        return '/admin/'

class AdminLogoutView(auth_views.LogoutView):
    next_page = '/admin/login/'
    http_method_names = ['post']  # 只允许POST请求

urlpatterns = [
    # Admin后台路由 - 自定义登录/退出路由要在admin.site.urls之前
    path('admin/login/', AdminLoginView.as_view()),
    path('admin/logout/', AdminLogoutView.as_view()),
    path('admin/', admin.site.urls),
    
    # 组织架构模块
    path('organize/', include('organize.urls')),
    
    # 任务模块
    path('tasks/', include('tasks.urls')),
    
    # 任务管理模块
    path('task_management/', include('task_management.urls', namespace='task_management')),
    
    # 消耗管理模块
    path('consumption/', include('consumption_management.urls', namespace='consumption_stats')),
    
    # 像素管理模块
    path('pixel_management/', include('pixel_management.urls', namespace='pixel_management')),
    
    # 日报管理模块
    path('daily_report_management/', include('daily_report_management.urls', namespace='daily_report_management')),
    
    # 数据分析模块
    path('data_analysis/', include('data_analysis.urls', namespace='data_analysis')),
    
    # 首页
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('accounts/', include('django.contrib.auth.urls')),
]
