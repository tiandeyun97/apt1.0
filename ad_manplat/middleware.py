from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404

class AdminRedirectMiddleware:
    """
    中间件：将管理员重定向到任务管理页面
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 仅处理已登录用户对管理界面的访问
        if request.user.is_authenticated and request.user.is_staff:
            path = request.path
            
            # 如果是访问admin首页，则重定向到任务管理页面
            if path == '/admin/' or path == '/admin':
                return redirect('admin:task_management_task_changelist')
                
        return self.get_response(request) 