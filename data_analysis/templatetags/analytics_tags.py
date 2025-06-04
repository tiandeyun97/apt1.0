from django import template

register = template.Library()

@register.filter(name='can_view_analytics')
def can_view_analytics(user):
    """
    模板标签：检查用户是否有权限访问数据分析功能
    用法: {% if user|can_view_analytics %}...{% endif %}
    """
    if not user.is_authenticated:
        return False
        
    # 硬编码检查用户角色
    return user.is_superuser or user.is_staff or user.groups.filter(name='运营').exists() 