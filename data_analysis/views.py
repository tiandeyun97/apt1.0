from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from consumption_management.models import TaskConsumption
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, F, Q

def is_admin_or_operator(user):
    """检查用户是否为管理员或运营角色"""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['管理员', '运营']).exists()

@user_passes_test(is_admin_or_operator)
def index(request):
    """数据分析首页"""
    return render(request, 'admin/data_analysis/index.html')

@user_passes_test(is_admin_or_operator)
def consumption_trend(request):
    """消费趋势分析页面"""
    return render(request, 'admin/data_analysis/consumption_trend.html')

@user_passes_test(is_admin_or_operator)
def optimizer_ranking(request):
    """优化师榜单排名页面"""
    return render(request, 'admin/data_analysis/optimizer_ranking.html')
