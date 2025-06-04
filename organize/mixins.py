from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class OrganizePermissionMixin(UserPassesTestMixin):
    """组织架构权限Mixin
    
    验证用户是否具有组织架构相关权限的Mixin。
    根据视图的model和action属性自动构建所需的权限字符串。
    
    使用方法:
        - 在视图类中继承此Mixin
        - 设置model属性（通常通过继承通用视图已设置）
        - 设置action属性（'view', 'add', 'change', 'delete'）
    
    权限格式:
        - '{app_label}.{action}_{model_name}'
        - 例如: 'organize.view_company'（组织架构|公司|查看）
    """
    def test_func(self):
        # 超级用户具有所有权限
        if self.request.user.is_superuser:
            return True
            
        # 获取当前视图对应的权限
        app_label = 'organize'
        model_name = self.model._meta.model_name
        action = self.action if hasattr(self, 'action') else 'view'
        required_perm = f'{app_label}.{action}_{model_name}'
        
        # 检查用户是否具有所需权限
        return self.request.user.has_perm(required_perm)

    def handle_no_permission(self):
        raise PermissionDenied("您没有执行此操作的权限。") 