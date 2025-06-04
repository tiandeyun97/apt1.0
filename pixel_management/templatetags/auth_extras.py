from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """检查用户是否属于指定组"""
    try:
        group = Group.objects.get(name=group_name)
        return True if group in user.groups.all() else False
    except Group.DoesNotExist:
        return False

@register.filter(name='has_perm')
def has_perm(user, perm_name):
    """检查用户是否拥有指定权限"""
    return user.has_perm(perm_name) 