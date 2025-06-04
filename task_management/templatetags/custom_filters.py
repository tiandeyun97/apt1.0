from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """
    将字符串按指定分隔符拆分为列表
    用法: {{ value|split:"," }}
    """
    if value:
        return value.split(delimiter)
    return [] 