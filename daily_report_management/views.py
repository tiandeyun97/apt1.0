from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import json
from .models import DailyReport
from task_management.permissions import TaskPermission
from task_management.models import Task


def daily_report_page(request):
    """日报管理页面"""
    # 不再预加载数据，完全由前端JavaScript负责
    return render(request, 'daily_report_management/daily_report_list.html')


@csrf_exempt
@require_http_methods(["GET"])
def daily_report_list(request):
    """获取日报列表的API，应用权限过滤"""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    # 获取过滤条件
    channel_name = request.GET.get('channel_name', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 基础查询
    reports = DailyReport.objects.all()
    
    # 应用用户权限过滤
    if not request.user.is_authenticated:
        # 未登录用户返回空数据
        reports = reports.none()
    elif not request.user.is_superuser:
        # 非管理员用户应用权限过滤
        # 使用TaskPermission获取用户可见的任务
        visible_tasks = TaskPermission.filter_tasks_by_role(Task.objects.all(), request.user)
        
        # 从可见任务中获取相关的channel_name
        channel_names = []
        for task in visible_tasks:
            if task.name:
                channel_names.append(task.name)
            if task.advert_name:
                channel_names.append(task.advert_name)
        
        # 如果没有找到任何可见的渠道，返回空查询集
        if not channel_names:
            reports = reports.none()
        else:
            # 构建查询条件，查找channel_name包含在可见任务列表中的日报
            filter_condition = Q()
            for name in channel_names:
                filter_condition |= Q(channel_name__icontains=name)
                
            reports = reports.filter(filter_condition).distinct()
    
    # 应用用户输入的筛选条件
    if channel_name:
        reports = reports.filter(channel_name__icontains=channel_name)
    if date_from:
        reports = reports.filter(date__gte=date_from)
    if date_to:
        reports = reports.filter(date__lte=date_to)
    
    # 排序
    reports = reports.order_by('-date')
    
    # 分页
    paginator = Paginator(reports, page_size)
    page_obj = paginator.get_page(page)
    
    # 构建返回数据
    data = [{
        'id': report.id,
        'date': report.date.strftime('%Y-%m-%d'),
        'channel_name': report.channel_name,
        'optimizers': report.optimizers,
        'consumption': float(report.consumption),
        'registrations': report.registrations,
        'first_deposits': report.first_deposits,
        'registration_cost': float(report.registration_cost),
        'first_deposit_cost': float(report.first_deposit_cost),
        'budget': float(report.budget),
        'kpi': report.kpi or '',
        'daily_recharge_rate': float(report.daily_recharge_rate),
        'retention_day2': float(report.retention_day2),
        'retention_day3': float(report.retention_day3),
        'retention_day4': float(report.retention_day4),
        'retention_day5': float(report.retention_day5),
        'retention_day7': float(report.retention_day7),
        'budget_description': report.budget_description or '',
        'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': report.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    } for report in page_obj]
    
    return JsonResponse({
        'code': 200,
        'message': '成功',
        'data': data,
        'total': paginator.count,
        'page': page,
        'page_size': page_size,
        'total_pages': paginator.num_pages,
    })


@csrf_exempt
@require_http_methods(["POST"])
def create_daily_report(request):
    """创建日报"""
    try:
        data = json.loads(request.body)
        report = DailyReport.objects.create(
            date=data.get('date'),
            channel_name=data.get('channel_name'),
            consumption=data.get('consumption'),
            registrations=data.get('registrations'),
            first_deposits=data.get('first_deposits'),
            budget=data.get('budget'),
            kpi=data.get('kpi'),
            daily_recharge_rate=data.get('daily_recharge_rate', 0),
            retention_day2=data.get('retention_day2', 0),
            retention_day3=data.get('retention_day3', 0),
            retention_day4=data.get('retention_day4', 0),
            retention_day5=data.get('retention_day5', 0),
            retention_day7=data.get('retention_day7', 0),
            budget_description=data.get('budget_description')
        )
        
        return JsonResponse({
            'code': 200,
            'message': '创建成功',
            'data': {
                'id': report.id,
                'date': report.date.strftime('%Y-%m-%d'),
                'channel_name': report.channel_name,
                'optimizers': report.optimizers,
                'consumption': float(report.consumption),
                'registrations': report.registrations,
                'first_deposits': report.first_deposits,
                'registration_cost': float(report.registration_cost),
                'first_deposit_cost': float(report.first_deposit_cost),
                'budget': float(report.budget),
                'kpi': report.kpi or '',
                'daily_recharge_rate': float(report.daily_recharge_rate),
                'retention_day2': float(report.retention_day2),
                'retention_day3': float(report.retention_day3),
                'retention_day4': float(report.retention_day4),
                'retention_day5': float(report.retention_day5),
                'retention_day7': float(report.retention_day7),
                'budget_description': report.budget_description or '',
                'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': report.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'创建失败: {str(e)}',
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_daily_report(request, report_id):
    """删除日报"""
    try:
        # 检查用户是否有权限删除此报告
        if not request.user.is_superuser:
            return JsonResponse({
                'code': 403,
                'message': '没有权限执行此操作',
            }, status=403)
            
        report = DailyReport.objects.get(id=report_id)
        report.delete()
        
        return JsonResponse({
            'code': 200,
            'message': '删除成功',
        })
    except DailyReport.DoesNotExist:
        return JsonResponse({
            'code': 404,
            'message': '日报不存在',
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'删除失败: {str(e)}',
        }, status=500)
