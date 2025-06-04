from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Avg, F, Count, Q
from django.contrib.auth.decorators import login_required
from task_management.models import Task
from .models import TaskConsumption
from django.http import JsonResponse
from django.shortcuts import redirect
import json
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from organize.models import Department, User
from .permissions import filter_queryset_by_role, check_task_consumption_permission

# 定义辅助函数用于处理默认日期过滤
def apply_default_date_filter(queryset, start_date=None, end_date=None):
    """
    应用默认的日期过滤逻辑
    如果未提供start_date，默认过滤最近60天的数据
    如果未提供end_date，使用当前日期作为结束日期
    
    返回: (过滤后的queryset, 开始日期字符串, 结束日期字符串)
    """
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
        start_date_str = start_date if isinstance(start_date, str) else start_date.strftime('%Y-%m-%d')
    else:
        # 默认显示最近60天
        default_start_date = timezone.now().date() - timedelta(days=60)
        queryset = queryset.filter(date__gte=default_start_date)
        start_date_str = default_start_date.strftime('%Y-%m-%d')
    
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
        end_date_str = end_date if isinstance(end_date, str) else end_date.strftime('%Y-%m-%d')
    else:
        end_date_str = timezone.now().date().strftime('%Y-%m-%d')
    
    return queryset, start_date_str, end_date_str

class TaskConsumptionListView(LoginRequiredMixin, ListView):
    model = TaskConsumption
    template_name = 'consumption_stats/task_consumption_list.html'
    context_object_name = 'consumptions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤特定任务的记录
        task_id = self.kwargs.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
            return queryset  # 如果是查看特定任务的消耗明细，则不做角色限制
        
        # 使用公共权限过滤函数
        return filter_queryset_by_role(queryset, self.request.user, "taskconsumption")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # 添加汇总数据
        summary = {
            'total_daily_consumption': queryset.aggregate(Sum('daily_consumption'))['daily_consumption__sum'] or 0,
            'total_return_flow': queryset.aggregate(Sum('return_flow'))['return_flow__sum'] or 0,
            'total_actual_consumption': queryset.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0,
            'total_registrations': queryset.aggregate(Sum('registrations'))['registrations__sum'] or 0,
            'total_first_deposits': queryset.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0,
            'total_impressions': queryset.aggregate(Sum('impressions'))['impressions__sum'] or 0,
            'total_clicks': queryset.aggregate(Sum('clicks'))['clicks__sum'] or 0,
        }
        
        # 添加任务信息
        task_id = self.kwargs.get('task_id')
        if task_id:
            context['task'] = get_object_or_404(Task, id=task_id)
        
        # 检测是否是内联请求
        is_inline = self.request.GET.get('inline', '0') == '1' or 'X-Requested-As-Inline' in self.request.headers
        context['is_inline'] = is_inline
        
        context['summary'] = summary
        return context

@login_required
def add_task_consumption(request, task_id):
    """添加特定任务消耗记录的视图"""
    task = get_object_or_404(Task, id=task_id)
    
    # 检查用户权限
    if not check_task_consumption_permission(request.user, task, "add"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': '您没有权限为此任务添加消耗记录'
            }, status=403)
        
        return render(request, 'consumption_stats/task_consumption_list.html', {
            'error_message': '您没有权限为此任务添加消耗记录'
        }, status=403)
    
    # 保存HTTP_REFERER以便返回时保留查询条件
    referer = request.META.get('HTTP_REFERER', '')
    
    if request.method == 'POST':
        # 处理表单提交
        try:
            # 检查是否是JSON格式的AJAX请求
            if request.headers.get('Content-Type') == 'application/json':
                # 解析JSON数据
                json_data = json.loads(request.body)
                
                # 创建消耗记录（使用正确的类型）
                consumption = TaskConsumption(
                    task=task,
                    creator=request.user,
                    date=json_data.get('date'),
                    daily_consumption=Decimal(json_data.get('daily_consumption', 0)),
                    return_flow=Decimal(json_data.get('return_flow', 0)),
                    registrations=int(json_data.get('registrations', 0)),
                    first_deposits=int(json_data.get('first_deposits', 0)),
                    impressions=int(json_data.get('impressions', 0)),
                    clicks=int(json_data.get('clicks', 0))
                )
            else:
                # 处理常规表单提交
                consumption = TaskConsumption(
                    task=task,
                    creator=request.user,
                    date=request.POST.get('date'),
                    daily_consumption=Decimal(request.POST.get('daily_consumption') or 0),
                    return_flow=Decimal(request.POST.get('return_flow') or 0),
                    registrations=int(request.POST.get('registrations') or 0),
                    first_deposits=int(request.POST.get('first_deposits') or 0),
                    impressions=int(request.POST.get('impressions') or 0),
                    clicks=int(request.POST.get('clicks') or 0)
                )
            
            # 保存记录
            consumption.save()
            
            # 返回JSON响应，不论是否为AJAX请求
            return JsonResponse({
                'success': True,
                'message': '消耗记录已保存',
                'consumption_id': str(consumption.id)
            })
        except Exception as e:
            # 处理错误
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET请求，查询当前任务的消耗记录列表
    consumptions = TaskConsumption.objects.filter(task_id=task_id)
    
    # 按日期筛选
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    creator_id = request.GET.get('creator')
    
    # 获取引用页面来源参数
    source = request.GET.get('source', '')
    
    if start_date:
        consumptions = consumptions.filter(date__gte=start_date)
    
    if end_date:
        consumptions = consumptions.filter(date__lte=end_date)
    
    if creator_id:
        consumptions = consumptions.filter(creator_id=creator_id)
    
    # 按日期降序排序
    consumptions = consumptions.order_by('-date')
    
    # 获取该任务下所有消耗记录的创建人列表（供筛选用）
    creators = User.objects.filter(
        created_consumptions__task_id=task_id
    ).distinct()
    
    # 计算汇总数据
    total_daily_consumption = consumptions.aggregate(Sum('daily_consumption'))['daily_consumption__sum'] or 0
    total_return_flow = consumptions.aggregate(Sum('return_flow'))['return_flow__sum'] or 0
    total_actual_consumption = consumptions.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
    total_registrations = consumptions.aggregate(Sum('registrations'))['registrations__sum'] or 0
    total_first_deposits = consumptions.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0
    total_impressions = consumptions.aggregate(Sum('impressions'))['impressions__sum'] or 0
    total_clicks = consumptions.aggregate(Sum('clicks'))['clicks__sum'] or 0
    
    # 显示表单，并传递消耗记录列表
    return render(request, 'consumption_stats/add_task_consumption.html', {
        'task': task,
        'consumptions': consumptions,
        'creators': creators,
        'from_consumption_list': source == 'consumption_list',
        'total_daily_consumption': total_daily_consumption,
        'total_return_flow': total_return_flow,
        'total_actual_consumption': total_actual_consumption,
        'total_registrations': total_registrations,
        'total_first_deposits': total_first_deposits,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'referer': referer  # 传递引用页面信息
    })

@login_required
def delete_task_consumption(request, task_id, consumption_id):
    """删除特定消耗记录的视图"""
    # 首先检查请求方法
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': '只支持POST请求方法'
            }, status=405)
        return redirect('consumption_stats:add_task_consumption', task_id=task_id)
    
    consumption = get_object_or_404(TaskConsumption, id=consumption_id, task_id=task_id)
    task = consumption.task
    
    # 检查用户权限
    if not check_task_consumption_permission(request.user, task, "delete"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': '您没有权限删除此记录'
            }, status=403)
        
        return render(request, 'consumption_stats/add_task_consumption.html', {
            'task': task,
            'error_message': '您没有权限删除此记录'
        }, status=403)
    
    try:
        consumption.delete()
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '消耗记录已删除'
            })
        
        # 正常请求重定向到添加消耗记录页面
        return redirect('consumption_stats:add_task_consumption', task_id=task_id)
    except Exception as e:
        # 处理错误
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        return render(request, 'consumption_stats/add_task_consumption.html', {
            'task': task,
            'error_message': f'删除失败: {str(e)}'
        })

@login_required
def edit_task_consumption(request, task_id, consumption_id):
    """编辑特定消耗记录的视图"""
    task = get_object_or_404(Task, id=task_id)
    consumption = get_object_or_404(TaskConsumption, id=consumption_id, task_id=task_id)
    
    # 检查用户权限
    if not check_task_consumption_permission(request.user, task, "edit"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': '您没有权限编辑此记录'
            }, status=403)
        
        return render(request, 'consumption_stats/task_consumption_list.html', {
            'error_message': '您没有权限编辑此记录'
        }, status=403)
    
    # 处理GET请求，返回记录数据
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': str(consumption.id),
            'date': consumption.date.strftime('%Y-%m-%d'),
            'daily_consumption': float(consumption.daily_consumption),
            'return_flow': float(consumption.return_flow),
            'registrations': consumption.registrations,
            'first_deposits': consumption.first_deposits,
            'impressions': consumption.impressions,
            'clicks': consumption.clicks
        }
        return JsonResponse({'success': True, 'data': data})
    
    # 处理POST请求，更新记录
    if request.method == 'POST':
        try:
            # 检查是否是JSON格式的AJAX请求
            if request.headers.get('Content-Type') == 'application/json':
                # 解析JSON数据
                json_data = json.loads(request.body)
                
                # 更新消耗记录
                consumption.date = json_data.get('date')
                consumption.daily_consumption = Decimal(json_data.get('daily_consumption', 0))
                consumption.return_flow = Decimal(json_data.get('return_flow', 0))
                consumption.registrations = int(json_data.get('registrations', 0))
                consumption.first_deposits = int(json_data.get('first_deposits', 0))
                consumption.impressions = int(json_data.get('impressions', 0))
                consumption.clicks = int(json_data.get('clicks', 0))
            else:
                # 处理常规表单提交
                consumption.date = request.POST.get('date')
                consumption.daily_consumption = Decimal(request.POST.get('daily_consumption') or 0)
                consumption.return_flow = Decimal(request.POST.get('return_flow') or 0)
                consumption.registrations = int(request.POST.get('registrations') or 0)
                consumption.first_deposits = int(request.POST.get('first_deposits') or 0)
                consumption.impressions = int(request.POST.get('impressions') or 0)
                consumption.clicks = int(request.POST.get('clicks') or 0)
            
            # 保存更新后的记录
            consumption.save()
            
            # 检查是否是AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '消耗记录已更新'
                })
            
            # 正常请求重定向到任务消耗列表页面
            return redirect('consumption_stats:task_consumption_list_by_task', task_id=task.id)
        except Exception as e:
            # 处理错误
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            return render(request, 'consumption_stats/task_consumption_list.html', {
                'error_message': f'更新失败: {str(e)}'
            })
    
    # 其他请求方法
    return render(request, 'consumption_stats/task_consumption_list.html', {
        'task': task,
        'consumption': consumption
    })

@login_required
def get_task_consumption(request, task_id, consumption_id):
    """获取特定消耗记录数据的视图"""
    task = get_object_or_404(Task, id=task_id)
    consumption = get_object_or_404(TaskConsumption, id=consumption_id, task_id=task_id)
    
    # 检查用户权限
    if not check_task_consumption_permission(request.user, task, "view"):
        return JsonResponse({
            'success': False,
            'error': '您没有权限查看此记录'
        }, status=403)
    
    # 返回记录数据
    data = {
        'id': str(consumption.id),
        'date': consumption.date.strftime('%Y-%m-%d'),
        'daily_consumption': float(consumption.daily_consumption),
        'return_flow': float(consumption.return_flow),
        'registrations': consumption.registrations,
        'first_deposits': consumption.first_deposits,
        'impressions': consumption.impressions,
        'clicks': consumption.clicks
    }
    
    return JsonResponse({
        'success': True,
        'data': data
    })

@login_required
def get_task_optimizers_count(request, task_id):
    """获取任务绑定的优化师数量"""
    task = get_object_or_404(Task, id=task_id)
    
    # 检查用户权限
    if not check_task_consumption_permission(request.user, task, "view"):
        return JsonResponse({
            'success': False,
            'error': '您没有权限查看此任务'
        }, status=403)
    
    # 获取优化师数量
    optimizer_count = task.optimizer.count()
    
    return JsonResponse({
        'success': True,
        'count': optimizer_count
    })

class ConsumptionAnalysisView(LoginRequiredMixin, TemplateView):
    """消耗数据分析视图"""
    template_name = 'consumption_stats/consumption_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 提前导入所需模型
        from task_management.models import Task
        from tasks.models import Project
        
        # 获取过滤参数
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        project_id = self.request.GET.get('project_id')
        task_id = self.request.GET.get('task_id')
        optimizer_id = self.request.GET.get('optimizer_id')
        
        # 获取用户有权限查看的任务列表
        task_queryset = Task.objects.all()
        task_queryset = filter_queryset_by_role(task_queryset, self.request.user, "taskconsumption")
        
        # 从任务列表中提取项目ID
        visible_project_ids = task_queryset.values_list('project_id', flat=True).distinct()
        
        # 根据项目ID获取可见的项目列表
        all_projects = Project.objects.filter(ProjectID__in=visible_project_ids).order_by('ProjectName')
        
        # 验证项目权限 - 如果用户选择了他们没有权限的项目，则忽略此选择
        if project_id:
            if str(project_id) not in [str(pid) for pid in visible_project_ids]:
                project_id = None
            else:
                context['selected_project'] = get_object_or_404(Project, ProjectID=project_id)
                
        # 验证任务权限 - 如果用户选择了他们没有权限的任务，则忽略此选择
        if task_id:
            visible_task_ids = task_queryset.values_list('id', flat=True)
            if str(task_id) not in [str(tid) for tid in visible_task_ids]:
                task_id = None
            else:
                context['selected_task'] = get_object_or_404(Task, id=task_id)
                
        # 根据所选项目过滤任务列表
        if project_id:
            all_tasks = task_queryset.filter(project_id=project_id).order_by('name')
        else:
            all_tasks = task_queryset.order_by('name')
        
        # 构建查询集
        queryset = TaskConsumption.objects.all()
        
        # 应用过滤条件
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        else:
            # 默认显示最近60天的数据
            default_start_date = timezone.now().date() - timedelta(days=60)
            queryset = queryset.filter(date__gte=default_start_date)
            context['date_from'] = default_start_date.strftime('%Y-%m-%d')
            
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        else:
            context['date_to'] = timezone.now().date().strftime('%Y-%m-%d')
        
        # 应用项目和任务过滤
        if project_id:
            queryset = queryset.filter(task__project_id=project_id)
            
        if task_id:
            queryset = queryset.filter(task_id=task_id)
            
        if optimizer_id:
            queryset = queryset.filter(Q(task__optimizer__id=optimizer_id) | Q(creator_id=optimizer_id))
        
        # 总体数据统计
        total_stats = {
            'total_daily_consumption': queryset.aggregate(Sum('daily_consumption'))['daily_consumption__sum'] or 0,
            'total_return_flow': queryset.aggregate(Sum('return_flow'))['return_flow__sum'] or 0,
            'total_actual_consumption': queryset.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0,
            'total_registrations': queryset.aggregate(Sum('registrations'))['registrations__sum'] or 0,
            'total_first_deposits': queryset.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0,
            'total_impressions': queryset.aggregate(Sum('impressions'))['impressions__sum'] or 0,
            'total_clicks': queryset.aggregate(Sum('clicks'))['clicks__sum'] or 0,
        }
        
        # 计算平均数据
        if queryset.count() > 0:
            avg_stats = {
                'avg_daily_consumption': queryset.aggregate(Avg('daily_consumption'))['daily_consumption__avg'] or 0,
                'avg_registrations': queryset.aggregate(Avg('registrations'))['registrations__avg'] or 0,
                'avg_first_deposits': queryset.aggregate(Avg('first_deposits'))['first_deposits__avg'] or 0,
            }
        else:
            avg_stats = {
                'avg_daily_consumption': 0,
                'avg_registrations': 0,
                'avg_first_deposits': 0,
            }
        
        # 计算KPI指标
        if total_stats['total_registrations'] > 0:
            avg_registration_cost = total_stats['total_actual_consumption'] / total_stats['total_registrations']
        else:
            avg_registration_cost = 0
            
        if total_stats['total_first_deposits'] > 0:
            avg_first_deposit_cost = total_stats['total_actual_consumption'] / total_stats['total_first_deposits']
        else:
            avg_first_deposit_cost = 0
            
        if total_stats['total_clicks'] > 0:
            avg_click_cost = total_stats['total_actual_consumption'] / total_stats['total_clicks']
        else:
            avg_click_cost = 0
        
        # 按日期进行分组统计 - 简化只保留图表所需的数据
        daily_stats = list(queryset.values('date').annotate(
            daily_sum=Sum('daily_consumption'),
            registration_sum=Sum('registrations'),
            first_deposit_sum=Sum('first_deposits'),
            impression_sum=Sum('impressions'),
            click_sum=Sum('clicks')
        ).order_by('date'))
        
        # 按任务分组统计
        task_stats = list(queryset.values('task__name').annotate(
            daily_sum=Sum('daily_consumption'),
            actual_consumption_sum=Sum('actual_consumption'),
            registration_sum=Sum('registrations'),
            first_deposit_sum=Sum('first_deposits'),
            impression_sum=Sum('impressions'),
            click_sum=Sum('clicks'),
            task_count=Count('task')
        ).order_by('-daily_sum'))
        
        # 按优化师分组统计
        optimizer_stats = list(queryset.values('creator__username').annotate(
            daily_sum=Sum('daily_consumption'),
            actual_consumption_sum=Sum('actual_consumption'),
            registration_sum=Sum('registrations'),
            first_deposit_sum=Sum('first_deposits'),
            impression_sum=Sum('impressions'),
            click_sum=Sum('clicks'),
            record_count=Count('id')
        ).order_by('-daily_sum'))
        
        # 将数据转换为JSON格式 - 仅用于图表渲染
        context['daily_stats_json'] = json.dumps(daily_stats, cls=DjangoJSONEncoder)
        context['task_stats_json'] = json.dumps(task_stats, cls=DjangoJSONEncoder)
        context['optimizer_stats_json'] = json.dumps(optimizer_stats, cls=DjangoJSONEncoder)
        
        # 添加到上下文
        context.update({
            'total_stats': total_stats,
            'avg_stats': avg_stats,
            'avg_registration_cost': avg_registration_cost,
            'avg_first_deposit_cost': avg_first_deposit_cost,
            'avg_click_cost': avg_click_cost,
            'task_stats': task_stats,
            'optimizer_stats': optimizer_stats,
            'all_tasks': all_tasks,
            'all_projects': all_projects,
            'queryset': queryset.order_by('-date')[:100],  # 限制最近的100条记录用于表格显示
        })
        
        return context

@login_required
def consumption_records_list(request):
    """
    显示所有消耗记录明细，基于用户权限进行过滤
    """
    # 获取筛选条件
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    project_id = request.GET.get('project_id')
    task_id = request.GET.get('task_id')
    creator_id = request.GET.get('creator_id')
    
    # 当前页码
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    # 初始查询集
    queryset = TaskConsumption.objects.all()
    
    # 应用默认日期过滤
    queryset, start_date, end_date = apply_default_date_filter(queryset, start_date, end_date)
    
    # 项目筛选
    if project_id:
        queryset = queryset.filter(task__project_id=project_id)
    
    # 任务筛选
    if task_id:
        queryset = queryset.filter(task_id=task_id)
    
    # 创建人筛选
    if creator_id:
        queryset = queryset.filter(creator_id=creator_id)
    else:
        # 检查用户角色，只有非管理员/运营/超级管理员才限制只看自己的数据
        is_admin_or_operator = request.user.is_superuser or request.user.groups.filter(name__in=['管理员', '运营']).exists()
        if not is_admin_or_operator:
            # 如果不是管理员/运营/超级管理员，则只显示当前用户创建的记录
            queryset = queryset.filter(creator=request.user)
    
    # 按照权限过滤数据
    queryset = filter_queryset_by_role(queryset, request.user, "taskconsumption")
    
    # 检查用户角色，只有非管理员/运营/超级管理员才限制只看自己的数据
    is_admin_or_operator = request.user.is_superuser or request.user.groups.filter(name__in=['管理员', '运营']).exists()
    if not is_admin_or_operator:
        # 如果不是管理员/运营/超级管理员，则只显示当前用户创建的记录
        queryset = queryset.filter(creator=request.user)
    
    # 按日期降序排序，并优化查询性能，使用select_related减少数据库查询
    queryset = queryset.select_related('task', 'task__project', 'creator').order_by('-date')
    
    # 获取任务和项目列表（根据权限过滤）
    task_queryset = Task.objects.all()
    task_queryset = filter_queryset_by_role(task_queryset, request.user, "task")
    
    # 获取项目列表
    from tasks.models import Project
    project_ids = task_queryset.values_list('project_id', flat=True).distinct()
    projects = Project.objects.filter(ProjectID__in=project_ids).order_by('ProjectName')
    
    # 准备任务列表
    if project_id:
        tasks = task_queryset.filter(project_id=project_id).order_by('name')
    else:
        tasks = task_queryset.order_by('name')
    
    # 获取创建人列表
    from organize.models import User
    # 获取所有有消耗记录的用户ID
    creator_ids = TaskConsumption.objects.values_list('creator_id', flat=True).distinct()
    creators = User.objects.filter(id__in=creator_ids).order_by('username')
    
    # 在分页前计算汇总统计数据
    filtered_queryset = queryset
    
    # 计算汇总统计数据
    summary = {
        'total_daily_consumption': filtered_queryset.aggregate(Sum('daily_consumption'))['daily_consumption__sum'] or 0,
        'total_return_flow': filtered_queryset.aggregate(Sum('return_flow'))['return_flow__sum'] or 0,
        'total_actual_consumption': filtered_queryset.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0,
        'total_registrations': filtered_queryset.aggregate(Sum('registrations'))['registrations__sum'] or 0,
        'total_first_deposits': filtered_queryset.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0,
        'total_impressions': filtered_queryset.aggregate(Sum('impressions'))['impressions__sum'] or 0,
        'total_clicks': filtered_queryset.aggregate(Sum('clicks'))['clicks__sum'] or 0,
    }
    
    # 实现分页功能
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(queryset, 20)  # 每页显示20条记录
    
    try:
        paginated_consumptions = paginator.page(page)
    except PageNotAnInteger:
        paginated_consumptions = paginator.page(1)
    except EmptyPage:
        paginated_consumptions = paginator.page(paginator.num_pages)
    
    # 准备上下文
    context = {
        'consumptions': paginated_consumptions,
        'projects': projects,
        'tasks': tasks,
        'creators': creators,
        'summary': summary,
        'selected_project_id': project_id,
        'selected_task_id': task_id,
        'selected_creator_id': creator_id,
        'start_date': start_date,
        'end_date': end_date,
        'paginator': paginator,
        'page_obj': paginated_consumptions,
        'is_paginated': True if paginator.num_pages > 1 else False,
        'total_records': paginator.count
    }
    
    # 添加总消耗、本月消耗和上月消耗的统计
    # 为了避免重复过滤，先获取基础查询集（按照权限过滤后的全部数据）
    base_queryset = filter_queryset_by_role(TaskConsumption.objects.all(), request.user, "taskconsumption")
    
    # 检查用户角色，只有非管理员/运营/超级管理员才限制只看自己的数据
    is_admin_or_operator = request.user.is_superuser or request.user.groups.filter(name__in=['管理员', '运营']).exists()
    if not is_admin_or_operator:
        # 如果不是管理员/运营/超级管理员，则只显示当前用户创建的记录
        base_queryset = base_queryset.filter(creator=request.user)
    
    # 计算总消耗
    total_consumption = base_queryset.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
    
    # 获取当前月份的范围
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    
    # 计算本月消耗
    current_month_consumption = base_queryset.filter(
        date__gte=first_day_of_month,
        date__lt=next_month
    ).aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
    
    # 计算上月消耗
    if first_day_of_month.month == 1:
        prev_month_start = first_day_of_month.replace(year=first_day_of_month.year - 1, month=12, day=1)
    else:
        prev_month_start = first_day_of_month.replace(month=first_day_of_month.month - 1, day=1)
    
    prev_month_consumption = base_queryset.filter(
        date__gte=prev_month_start,
        date__lt=first_day_of_month
    ).aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
    
    # 添加到上下文
    context.update({
        'total_consumption': total_consumption,
        'current_month_consumption': current_month_consumption,
        'prev_month_consumption': prev_month_consumption
    })
    
    # 计算当日和昨日消耗
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # 计算当日实际消耗
    today_consumption = base_queryset.filter(
        date=today
    ).aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
    
    # 计算昨日实际消耗
    yesterday_consumption = base_queryset.filter(
        date=yesterday
    ).aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
    
    # 添加当日和昨日消耗到上下文
    context.update({
        'today_consumption': today_consumption,
        'yesterday_consumption': yesterday_consumption
    })
    
    return render(request, 'consumption_stats/consumption_records_list.html', context)

@login_required
def project_view_data(request):
    """获取按项目分组的消耗记录数据，用于项目视图"""
    # 导入所需模型
    from tasks.models import Project
    from task_management.models import Task
    
    # 获取筛选条件
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    project_id = request.GET.get('project_id')
    task_id = request.GET.get('task_id')
    creator_id = request.GET.get('creator_id')
    
    # 获取请求的数据类型
    data_type = request.GET.get('data_type', 'summary')
    
    # 创建基础查询集
    queryset = TaskConsumption.objects.all()
    
    # 使用权限过滤
    queryset = filter_queryset_by_role(queryset, request.user, "taskconsumption")
    
    # 根据用户角色判断是否只显示自己创建的数据
    # 检查用户角色，只有非管理员/运营/超级管理员才限制只看自己的数据
    is_admin_or_operator = request.user.is_superuser or request.user.groups.filter(name__in=['管理员', '运营']).exists()
    
    # 创建人筛选
    if creator_id:
        queryset = queryset.filter(creator_id=creator_id)
    elif not is_admin_or_operator:
        # 如果不是管理员/运营/超级管理员，且未指定创建人，则只显示当前用户创建的记录
        queryset = queryset.filter(creator=request.user)
    
    # 应用默认日期过滤
    queryset, _, _ = apply_default_date_filter(queryset, start_date, end_date)
    
    # 根据数据类型提供不同的响应
    if data_type == 'summary':
        # 只获取项目摘要信息，不加载详细数据
        
        # 计算总计数据
        total_consumption = queryset.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
        total_registrations = queryset.aggregate(Sum('registrations'))['registrations__sum'] or 0
        total_first_deposits = queryset.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0
        
        # 获取所有相关的项目
        project_ids = queryset.values_list('task__project_id', flat=True).distinct()
        projects_data = []
        
        # 对每个项目进行处理，只获取摘要数据
        for p_id in project_ids:
            project = Project.objects.get(ProjectID=p_id)
            project_consumptions = queryset.filter(task__project_id=p_id)
            
            # 计算项目汇总数据
            project_total_consumption = project_consumptions.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
            project_total_registrations = project_consumptions.aggregate(Sum('registrations'))['registrations__sum'] or 0
            project_total_first_deposits = project_consumptions.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0
            
            # 计算项目下的任务数
            task_count = project_consumptions.values('task_id').distinct().count()
            
            # 添加项目数据
            projects_data.append({
                'id': str(project.ProjectID),
                'name': project.ProjectName,
                'total_consumption': float(project_total_consumption),
                'total_registrations': project_total_registrations,
                'total_first_deposits': project_total_first_deposits,
                'task_count': task_count
            })
        
        # 准备响应数据
        response_data = {
            'total_consumption': float(total_consumption),
            'total_registrations': total_registrations,
            'total_first_deposits': total_first_deposits,
            'projects': projects_data
        }
        
        return JsonResponse(response_data)
        
    elif data_type == 'tasks':
        # 获取特定项目下的任务数据，但不包含消耗记录详情
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': '缺少项目ID参数'
            }, status=400)
            
        # 筛选特定项目的数据
        project_queryset = queryset.filter(task__project_id=project_id)
        
        # 获取项目下的所有任务
        task_ids = project_queryset.values_list('task_id', flat=True).distinct()
        tasks_data = []
        
        # 对每个任务进行处理
        for t_id in task_ids:
            task = Task.objects.get(id=t_id)
            task_consumptions = project_queryset.filter(task_id=t_id)
            
            # 计算任务汇总数据
            task_total_consumption = task_consumptions.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
            task_total_registrations = task_consumptions.aggregate(Sum('registrations'))['registrations__sum'] or 0
            task_total_first_deposits = task_consumptions.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0
            
            # 添加任务数据
            tasks_data.append({
                'id': str(task.id),
                'name': task.name,
                'total_consumption': float(task_total_consumption),
                'total_registrations': task_total_registrations,
                'total_first_deposits': task_total_first_deposits
            })
        
        # 准备响应数据
        response_data = {
            'tasks': tasks_data
        }
        
        return JsonResponse(response_data)
        
    elif data_type == 'records':
        # 获取特定任务的消耗记录详情
        if not task_id:
            return JsonResponse({
                'success': False,
                'error': '缺少任务ID参数'
            }, status=400)
            
        # 筛选特定任务的数据
        task_queryset = queryset.filter(task_id=task_id)
        
        # 计算任务汇总数据
        total_daily_consumption = task_queryset.aggregate(Sum('daily_consumption'))['daily_consumption__sum'] or 0
        total_return_flow = task_queryset.aggregate(Sum('return_flow'))['return_flow__sum'] or 0
        total_consumption = task_queryset.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0
        total_registrations = task_queryset.aggregate(Sum('registrations'))['registrations__sum'] or 0
        total_first_deposits = task_queryset.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0
        total_clicks = task_queryset.aggregate(Sum('clicks'))['clicks__sum'] or 0
        
        # 准备任务消耗记录数据
        records_data = []
        for record in task_queryset.order_by('-date'):
            records_data.append({
                'id': str(record.id),
                'date': record.date.strftime('%Y-%m-%d'),
                'daily_consumption': float(record.daily_consumption),
                'return_flow': float(record.return_flow),
                'actual_consumption': float(record.actual_consumption),
                'registrations': record.registrations,
                'first_deposits': record.first_deposits,
                'clicks': record.clicks,
                'registration_cost': float(record.registration_cost) if record.registrations > 0 else '-',
                'first_deposit_cost': float(record.first_deposit_cost) if record.first_deposits > 0 else '-',
            })
        
        # 准备响应数据
        response_data = {
            'total_daily_consumption': float(total_daily_consumption),
            'total_return_flow': float(total_return_flow),
            'total_consumption': float(total_consumption),
            'total_registrations': total_registrations,
            'total_first_deposits': total_first_deposits,
            'total_clicks': total_clicks,
            'records': records_data
        }
        
        return JsonResponse(response_data)
    
    else:
        # 不支持的数据类型
        return JsonResponse({
            'success': False,
            'error': '不支持的数据类型'
        }, status=400)

@login_required
def export_excel(request):
    """
    导出消耗记录为Excel文件
    使用与列表页相同的筛选条件
    """
    import pandas as pd
    import io
    from django.http import HttpResponse
    
    # 获取筛选条件，与consumption_records_list相同
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    project_id = request.GET.get('project_id')
    task_id = request.GET.get('task_id')
    creator_id = request.GET.get('creator_id')
    
    # 初始查询集
    queryset = TaskConsumption.objects.all()
    
    # 应用默认日期过滤
    queryset, start_date, end_date = apply_default_date_filter(queryset, start_date, end_date)
    
    # 项目筛选
    if project_id:
        queryset = queryset.filter(task__project_id=project_id)
    
    # 任务筛选
    if task_id:
        queryset = queryset.filter(task_id=task_id)
    
    # 创建人筛选
    if creator_id:
        queryset = queryset.filter(creator_id=creator_id)
    else:
        # 检查用户角色，只有非管理员/运营/超级管理员才限制只看自己的数据
        is_admin_or_operator = request.user.is_superuser or request.user.groups.filter(name__in=['管理员', '运营']).exists()
        if not is_admin_or_operator:
            # 如果不是管理员/运营/超级管理员，则只显示当前用户创建的记录
            queryset = queryset.filter(creator=request.user)
    
    # 按照权限过滤数据
    queryset = filter_queryset_by_role(queryset, request.user, "taskconsumption")
    
    # 检查用户角色，只有非管理员/运营/超级管理员才限制只看自己的数据
    is_admin_or_operator = request.user.is_superuser or request.user.groups.filter(name__in=['管理员', '运营']).exists()
    if not is_admin_or_operator:
        # 如果不是管理员/运营/超级管理员，则只显示当前用户创建的记录
        queryset = queryset.filter(creator=request.user)
    
    # 按日期降序排序，使用select_related减少数据库查询
    queryset = queryset.select_related('task', 'task__project', 'creator').order_by('-date')
    
    # 创建一个字典列表，用于创建DataFrame
    data = []
    for consumption in queryset:
        data.append({
            '日期': consumption.date.strftime('%Y-%m-%d'),
            '任务名称': consumption.task.name,
            '项目': consumption.task.project.ProjectName if consumption.task.project else '',
            '当日消耗': float(consumption.daily_consumption),
            '回流': float(consumption.return_flow),
            '实际消耗': float(consumption.actual_consumption),
            '回流占比': float(consumption.return_flow_ratio),
            '展示量': consumption.impressions,
            '点击量': consumption.clicks,
            '点击转化率': float(consumption.click_conversion_rate),
            '点击成本': float(consumption.click_cost),
            '注册人数': consumption.registrations,
            '注册转化率': float(consumption.registration_conversion_rate),
            '注册成本': float(consumption.registration_cost),
            '首充人数': consumption.first_deposits,
            '首充转化率': float(consumption.first_deposit_conversion_rate),
            '首充成本': float(consumption.first_deposit_cost),
            'ECPM': float(consumption.ecpm),
            '创建人': consumption.creator.username if consumption.creator else ''
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 添加合计行
    summary = {
        '日期': '合计',
        '任务名称': '',
        '项目': '',
        '当日消耗': float(queryset.aggregate(Sum('daily_consumption'))['daily_consumption__sum'] or 0),
        '回流': float(queryset.aggregate(Sum('return_flow'))['return_flow__sum'] or 0),
        '实际消耗': float(queryset.aggregate(Sum('actual_consumption'))['actual_consumption__sum'] or 0),
        '回流占比': '',
        '展示量': queryset.aggregate(Sum('impressions'))['impressions__sum'] or 0,
        '点击量': queryset.aggregate(Sum('clicks'))['clicks__sum'] or 0,
        '点击转化率': '',
        '点击成本': '',
        '注册人数': queryset.aggregate(Sum('registrations'))['registrations__sum'] or 0,
        '注册转化率': '',
        '注册成本': '',
        '首充人数': queryset.aggregate(Sum('first_deposits'))['first_deposits__sum'] or 0,
        '首充转化率': '',
        '首充成本': '',
        'ECPM': '',
        '创建人': ''
    }
    
    # 将合计行添加到DataFrame
    df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)
    
    # 创建文件名，使用简单的消耗记录+时间格式
    current_time = timezone.now().strftime('%Y%m%d%H%M%S')
    filename = f"消耗记录_{current_time}.xlsx"
    
    # 创建Excel写入器
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='消耗记录', index=False)
        
        # 获取工作簿和工作表对象
        workbook = writer.book
        worksheet = writer.sheets['消耗记录']
        
        # 定义格式
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # 货币格式
        money_format = workbook.add_format({'num_format': '¥#,##0.00'})
        
        # 百分比格式
        percent_format = workbook.add_format({'num_format': '0.00%'})
        
        # 应用样式到标题行
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # 设置列宽
        worksheet.set_column('A:A', 12)  # 日期
        worksheet.set_column('B:B', 25)  # 任务名称
        worksheet.set_column('C:C', 20)  # 项目
        worksheet.set_column('D:F', 12, money_format)  # 消耗金额列
        worksheet.set_column('G:G', 10, percent_format)  # 回流占比
        worksheet.set_column('H:I', 12)  # 展示量、点击量
        worksheet.set_column('J:J', 10, percent_format)  # 点击转化率
        worksheet.set_column('K:K', 12, money_format)  # 点击成本
        worksheet.set_column('L:L', 10)  # 注册人数
        worksheet.set_column('M:M', 10, percent_format)  # 注册转化率
        worksheet.set_column('N:N', 12, money_format)  # 注册成本
        worksheet.set_column('O:O', 10)  # 首充人数
        worksheet.set_column('P:P', 10, percent_format)  # 首充转化率
        worksheet.set_column('Q:Q', 12, money_format)  # 首充成本
        worksheet.set_column('R:R', 12, money_format)  # ECPM
        worksheet.set_column('S:S', 15)  # 创建人
        
        # 冻结窗格
        worksheet.freeze_panes(1, 0)
    
    # 设置文件指针到开头
    buffer.seek(0)
    
    # 创建HTTP响应
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # 对文件名进行编码，确保正确显示中文
    import urllib.parse
    encoded_filename = urllib.parse.quote(filename)
    response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    
    return response

@login_required
def download_import_template(request):
    """
    下载消耗记录导入模板
    """
    import pandas as pd
    import io
    from django.http import HttpResponse
    from task_management.models import Task
    from organize.models import User
    from tasks.models import Project
    
    # 获取可选的任务列表（根据用户权限）
    task_queryset = Task.objects.all()
    task_queryset = filter_queryset_by_role(task_queryset, request.user, "task")
    
    # 获取前10个任务作为示例
    sample_tasks = list(task_queryset.values_list('name', flat=True).order_by('name')[:10])
    sample_tasks_text = "、".join(sample_tasks) if sample_tasks else "暂无任务"
    
    # 获取前10个项目作为示例
    project_ids = task_queryset.values_list('project_id', flat=True).distinct()[:10]
    sample_projects = list(Project.objects.filter(ProjectID__in=project_ids).values_list('ProjectName', flat=True))
    sample_projects_text = "、".join(sample_projects) if sample_projects else "暂无项目"
    
    # 获取创建人示例
    sample_users = list(User.objects.filter(company=request.user.company).values_list('username', flat=True)[:10])
    sample_users_text = "、".join(sample_users) if sample_users else "暂无用户"
    
    # 创建示例数据
    data = []
    
    # 示例行
    data.append({
        '任务名称(必填)': '示例任务名称',
        '项目(可选)': '示例项目名称',
        '日期(必填,格式:YYYY-MM-DD)': '2025-05-15',
        '当日消耗(必填,数字)': 12.00,
        '回流(可选,数字)': 0.00,
        '展示量(可选,整数)': 1000,
        '点击量(可选,整数)': 100,
        '注册人数(可选,整数)': 10,
        '首充人数(可选,整数)': 5,
        '创建人(可选)': request.user.username
    })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建Excel写入器
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='导入模板', index=False)
        
        # 获取工作簿和工作表对象
        workbook = writer.book
        worksheet = writer.sheets['导入模板']
        
        # 定义格式
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # 应用样式到标题行
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # 设置列宽
        worksheet.set_column('A:A', 30)  # 任务名称
        worksheet.set_column('B:B', 30)  # 项目
        worksheet.set_column('C:C', 25)  # 日期
        worksheet.set_column('D:E', 15)  # 当日消耗、回流
        worksheet.set_column('F:H', 15)  # 其他指标
        worksheet.set_column('I:I', 20)  # 创建人
        
        # 添加说明信息到新工作表
        instruction_sheet = workbook.add_worksheet('使用说明')
        instruction_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top'
        })
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4472C4',
            'font_color': 'white'
        })
        
        instruction_sheet.merge_range('A1:D1', '消耗记录导入模板使用说明', title_format)
        instruction_sheet.set_column('A:A', 15)
        instruction_sheet.set_column('B:D', 25)
        
        instructions = [
            ['字段', '说明', '格式要求', '示例值'],
            ['任务名称', '必填，必须是系统中存在的任务名称', '字符串', sample_tasks_text],
            ['项目', '可选，如填写必须是系统中存在的项目名称，如不填将使用任务关联的项目', '字符串', sample_projects_text],
            ['日期', '必填，记录的日期', 'YYYY-MM-DD格式', '2025-05-15'],
            ['当日消耗', '必填，当日消耗金额', '数字，最多两位小数', '12.00'],
            ['回流', '可选，回流金额', '数字，最多两位小数', '0.00'],
            ['展示量', '可选，广告展示次数', '整数', '1000'],
            ['点击量', '可选，广告点击次数', '整数', '100'],
            ['注册人数', '可选，用户注册数量', '整数', '10'],
            ['首充人数', '可选，首次充值用户数量', '整数', '5'],
            ['创建人', '可选，如不填则使用导入用户作为创建人', '系统中存在的用户名', sample_users_text]
        ]
        
        # 写入说明表头
        for col_num, value in enumerate(instructions[0]):
            instruction_sheet.write(1, col_num, value, header_format)
        
        # 写入说明内容
        for row_num, row in enumerate(instructions[1:], 2):
            for col_num, value in enumerate(row):
                instruction_sheet.write(row_num, col_num, value, instruction_format)
        
        # 添加注意事项
        instruction_sheet.merge_range('A14:D14', '注意事项', title_format)
        notes = [
            '1. 导入前请确保任务名称在系统中存在，否则导入将失败',
            '2. 如果填写项目名称，请确保项目在系统中存在',
            '3. 如果填写创建人，请确保创建人在系统中存在',
            '4. 日期格式必须为YYYY-MM-DD，例如2025-05-15',
            '5. 如果同一任务同一日期已存在数据，系统会提示是否覆盖',
            '6. 当日消耗字段必须填写大于0的数值',
            '7. 可选字段如不填写将默认为0',
            '8. 一次最多可导入1000条记录',
            '9. 导入过程中如有错误，系统会指出具体错误行和原因',
            '10. 每个任务在同一天的记录数不能超过优化师数量'
        ]
        
        for i, note in enumerate(notes, 15):
            instruction_sheet.merge_range(f'A{i}:D{i}', note, instruction_format)
    
    # 设置文件指针到开头
    buffer.seek(0)
    
    # 创建HTTP响应
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # 文件名
    filename = f"消耗记录导入模板.xlsx"
    
    # 对文件名进行编码，确保正确显示中文
    import urllib.parse
    encoded_filename = urllib.parse.quote(filename)
    response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    
    return response

@login_required
def import_consumptions(request):
    """
    导入消耗记录数据
    """
    from io import BytesIO
    import pandas as pd
    from django.contrib import messages
    from django.db import transaction
    from datetime import datetime
    from decimal import Decimal, InvalidOperation
    from task_management.models import Task
    from organize.models import User
    from tasks.models import Project
    
    if request.method != 'POST':
        return redirect('consumption_stats:consumption_records_list')
    
    # 检查用户权限
    is_admin_or_operator = request.user.is_superuser or request.user.groups.filter(name__in=['管理员', '运营']).exists()
    if not is_admin_or_operator:
        messages.error(request, "您没有权限导入消耗记录")
        return redirect('consumption_stats:consumption_records_list')
    
    # 检查是否上传了文件
    if 'import_file' not in request.FILES:
        messages.error(request, "请选择要导入的Excel文件")
        return redirect('consumption_stats:consumption_records_list')
    
    excel_file = request.FILES['import_file']
    
    # 检查文件类型
    if not excel_file.name.endswith(('.xlsx', '.xls')):
        messages.error(request, "文件格式不支持，请上传Excel文件(.xlsx或.xls)")
        return redirect('consumption_stats:consumption_records_list')
    
    # 读取Excel文件
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
    except Exception as e:
        messages.error(request, f"无法读取Excel文件: {str(e)}")
        return redirect('consumption_stats:consumption_records_list')
    
    # 检查必要的列是否存在
    required_columns = ['任务名称(必填)', '日期(必填,格式:YYYY-MM-DD)', '当日消耗(必填,数字)']
    for column in required_columns:
        if column not in df.columns:
            messages.error(request, f"Excel文件缺少必要的列: {column}")
            return redirect('consumption_stats:consumption_records_list')
    
    # 获取任务和项目列表（为了验证名称）
    tasks = {task.name: task for task in Task.objects.all()}
    projects = {project.ProjectName: project for project in Project.objects.all()}
    users = {user.username: user for user in User.objects.filter(company=request.user.company)}
    
    # 验证数据
    errors = []
    valid_records = []
    existing_records = []
    
    # 按任务-日期分组的记录计数
    task_date_count = {}
    
    # 跟踪总行数和错误行数
    total_rows = len(df)
    error_rows = 0
    
    for index, row in df.iterrows():
        row_num = index + 2  # Excel行号（加2因为0-indexed和标题行）
        
        # 任务名称验证
        task_name = str(row['任务名称(必填)']).strip()
        if pd.isna(task_name) or task_name == '':
            errors.append(f"第{row_num}行: 任务名称不能为空")
            error_rows += 1
            continue
            
        if task_name not in tasks:
            errors.append(f"第{row_num}行: 任务名称 '{task_name}' 在系统中不存在")
            error_rows += 1
            continue
        
        task = tasks[task_name]
        
        # 项目验证（可选）
        project = task.project  # 默认使用任务关联的项目
        if '项目(可选)' in df.columns and not pd.isna(row['项目(可选)']) and row['项目(可选)'] != '':
            project_name = str(row['项目(可选)']).strip()
            if project_name not in projects:
                errors.append(f"第{row_num}行: 项目名称 '{project_name}' 在系统中不存在")
                error_rows += 1
                continue
            project = projects[project_name]
        
        # 创建人验证（可选）
        creator = request.user  # 默认使用当前用户
        if '创建人(可选)' in df.columns and not pd.isna(row['创建人(可选)']) and row['创建人(可选)'] != '':
            creator_name = str(row['创建人(可选)']).strip()
            if creator_name not in users:
                errors.append(f"第{row_num}行: 创建人 '{creator_name}' 在系统中不存在")
                error_rows += 1
                continue
            creator = users[creator_name]
        
        # 日期验证
        date_str = str(row['日期(必填,格式:YYYY-MM-DD)']).strip()
        try:
            if isinstance(row['日期(必填,格式:YYYY-MM-DD)'], datetime):
                consumption_date = row['日期(必填,格式:YYYY-MM-DD)'].date()
            else:
                consumption_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append(f"第{row_num}行: 日期 '{date_str}' 格式错误，应为YYYY-MM-DD")
            error_rows += 1
            continue
        
        # 检查当日消耗
        try:
            daily_consumption = row['当日消耗(必填,数字)']
            if pd.isna(daily_consumption):
                errors.append(f"第{row_num}行: 当日消耗不能为空")
                error_rows += 1
                continue
                
            daily_consumption = Decimal(str(daily_consumption))
            if daily_consumption <= 0:
                errors.append(f"第{row_num}行: 当日消耗必须大于0")
                error_rows += 1
                continue
        except (InvalidOperation, ValueError):
            errors.append(f"第{row_num}行: 当日消耗 '{row['当日消耗(必填,数字)']}' 必须是有效的数字")
            error_rows += 1
            continue
        
        # 验证其他可选字段
        try:
            return_flow = Decimal(str(row.get('回流(可选,数字)', 0))) if not pd.isna(row.get('回流(可选,数字)', 0)) else Decimal('0')
            impressions = int(row.get('展示量(可选,整数)', 0)) if not pd.isna(row.get('展示量(可选,整数)', 0)) else 0
            clicks = int(row.get('点击量(可选,整数)', 0)) if not pd.isna(row.get('点击量(可选,整数)', 0)) else 0
            registrations = int(row.get('注册人数(可选,整数)', 0)) if not pd.isna(row.get('注册人数(可选,整数)', 0)) else 0
            first_deposits = int(row.get('首充人数(可选,整数)', 0)) if not pd.isna(row.get('首充人数(可选,整数)', 0)) else 0
        except (ValueError, TypeError, InvalidOperation):
            errors.append(f"第{row_num}行: 数值字段格式错误")
            error_rows += 1
            continue
        
        # 检查该任务-日期组合是否已存在
        key = (task.id, consumption_date)
        if key in task_date_count:
            task_date_count[key] += 1
        else:
            task_date_count[key] = 1
            
        # 检查该任务-日期组合是否已经存在于数据库中
        existing = TaskConsumption.objects.filter(task=task, date=consumption_date).exists()
        
        # 如果已存在，加入到覆盖列表
        if existing:
            existing_records.append(f"{task_name} - {consumption_date}")
        
        # 添加到有效记录列表
        valid_records.append({
            'task': task,
            'project': project,
            'creator': creator,
            'date': consumption_date,
            'daily_consumption': daily_consumption,
            'return_flow': return_flow,
            'impressions': impressions,
            'clicks': clicks,
            'registrations': registrations,
            'first_deposits': first_deposits
        })
    
    # 检查任务-日期组合中是否有超过优化师数量的记录
    for (task_id, date), count in task_date_count.items():
        task = Task.objects.get(id=task_id)
        optimizer_count = task.optimizer.count()
        if optimizer_count > 0 and count > optimizer_count:
            task_name = task.name
            errors.append(f"任务 '{task_name}' 在 {date} 的记录数({count})超过了优化师数量({optimizer_count})")
    
    # 如果有错误，返回错误信息
    if errors:
        error_message = "<br>".join(errors)
        messages.error(request, f"导入过程中发现以下错误:<br>{error_message}")
        return redirect('consumption_stats:consumption_records_list')
    
    # 如果有需要覆盖的记录，且用户没有确认覆盖，则显示确认页面
    if existing_records and request.POST.get('confirm_overwrite') != 'yes':
        # 将数据保存到会话中，以便用户确认后使用
        request.session['import_data'] = {
            'valid_records': [{'task_id': str(record['task'].id), 
                              'project_id': str(record['project'].ProjectID) if record['project'] else None,
                              'creator_id': str(record['creator'].id),
                              'date': record['date'].isoformat(),
                              'daily_consumption': str(record['daily_consumption']),
                              'return_flow': str(record['return_flow']),
                              'impressions': record['impressions'],
                              'clicks': record['clicks'],
                              'registrations': record['registrations'],
                              'first_deposits': record['first_deposits']} 
                              for record in valid_records]
        }
        
        context = {
            'existing_records': existing_records,
            'total_records': len(valid_records),
            'existing_count': len(existing_records)
        }
        
        return render(request, 'consumption_stats/confirm_import.html', context)
    
    # 执行导入
    imported_count = 0
    updated_count = 0
    
    try:
        with transaction.atomic():
            for record in valid_records:
                task = record['task']
                date = record['date']
                
                # 检查记录是否已存在
                existing_record = TaskConsumption.objects.filter(task=task, date=date).first()
                
                if existing_record:
                    # 更新已存在的记录
                    existing_record.daily_consumption = record['daily_consumption']
                    existing_record.return_flow = record['return_flow']
                    existing_record.impressions = record['impressions']
                    existing_record.clicks = record['clicks']
                    existing_record.registrations = record['registrations']
                    existing_record.first_deposits = record['first_deposits']
                    existing_record.creator = record['creator']
                    existing_record.save()
                    updated_count += 1
                else:
                    # 创建新记录
                    TaskConsumption.objects.create(
                        task=task,
                        date=date,
                        daily_consumption=record['daily_consumption'],
                        return_flow=record['return_flow'],
                        impressions=record['impressions'],
                        clicks=record['clicks'],
                        registrations=record['registrations'],
                        first_deposits=record['first_deposits'],
                        creator=record['creator']
                    )
                    imported_count += 1
    except Exception as e:
        messages.error(request, f"导入过程中发生错误: {str(e)}")
        return redirect('consumption_stats:consumption_records_list')
    
    # 清除会话数据
    if 'import_data' in request.session:
        del request.session['import_data']
    
    # 显示成功信息
    messages.success(request, f"成功导入 {imported_count} 条新记录，更新 {updated_count} 条已存在的记录。")
    
    return redirect('consumption_stats:consumption_records_list')

@login_required
def confirm_import(request):
    """
    确认导入已存在的记录
    """
    from django.contrib import messages
    from django.db import transaction
    from datetime import datetime
    from decimal import Decimal
    from task_management.models import Task
    from organize.models import User
    from tasks.models import Project
    
    if request.method != 'POST':
        return redirect('consumption_stats:consumption_records_list')
    
    # 检查会话中是否有导入数据
    if 'import_data' not in request.session:
        messages.error(request, "导入会话已过期，请重新上传文件")
        return redirect('consumption_stats:consumption_records_list')
    
    # 获取导入数据
    import_data = request.session['import_data']
    valid_records = import_data['valid_records']
    
    # 检查用户的选择
    if request.POST.get('action') == 'cancel':
        # 用户取消导入
        del request.session['import_data']
        messages.info(request, "导入已取消")
        return redirect('consumption_stats:consumption_records_list')
    
    # 用户确认导入，执行导入操作
    imported_count = 0
    updated_count = 0
    
    try:
        with transaction.atomic():
            for record_data in valid_records:
                task = Task.objects.get(id=record_data['task_id'])
                
                # 处理项目 (可能为None)
                project = None
                if record_data.get('project_id'):
                    project = Project.objects.get(ProjectID=record_data['project_id'])
                else:
                    project = task.project
                
                # 获取创建人
                creator = User.objects.get(id=record_data['creator_id'])
                
                date = datetime.fromisoformat(record_data['date']).date()
                daily_consumption = Decimal(record_data['daily_consumption'])
                return_flow = Decimal(record_data['return_flow'])
                impressions = record_data['impressions']
                clicks = record_data['clicks']
                registrations = record_data['registrations']
                first_deposits = record_data['first_deposits']
                
                # 检查记录是否已存在
                existing_record = TaskConsumption.objects.filter(task=task, date=date).first()
                
                if existing_record:
                    # 更新已存在的记录
                    existing_record.daily_consumption = daily_consumption
                    existing_record.return_flow = return_flow
                    existing_record.impressions = impressions
                    existing_record.clicks = clicks
                    existing_record.registrations = registrations
                    existing_record.first_deposits = first_deposits
                    existing_record.creator = creator
                    existing_record.save()
                    updated_count += 1
                else:
                    # 创建新记录
                    TaskConsumption.objects.create(
                        task=task,
                        date=date,
                        daily_consumption=daily_consumption,
                        return_flow=return_flow,
                        impressions=impressions,
                        clicks=clicks,
                        registrations=registrations,
                        first_deposits=first_deposits,
                        creator=creator
                    )
                    imported_count += 1
    except Exception as e:
        messages.error(request, f"导入过程中发生错误: {str(e)}")
        return redirect('consumption_stats:consumption_records_list')
    
    # 清除会话数据
    del request.session['import_data']
    
    # 显示成功信息
    messages.success(request, f"成功导入 {imported_count} 条新记录，更新 {updated_count} 条已存在的记录。")
    
    return redirect('consumption_stats:consumption_records_list')

@login_required
def search_projects(request):
    """项目模糊搜索API视图"""
    from tasks.models import Project
    
    # 获取搜索关键词
    search_term = request.GET.get('term', '')
    
    # 获取用户有权限查看的任务列表
    task_queryset = Task.objects.all()
    task_queryset = filter_queryset_by_role(task_queryset, request.user, "task")
    
    # 从任务列表中提取项目ID
    visible_project_ids = task_queryset.values_list('project_id', flat=True).distinct()
    
    # 构建项目查询集
    if search_term:
        # 使用模糊查询
        project_queryset = Project.objects.filter(
            ProjectID__in=visible_project_ids,
            ProjectName__icontains=search_term
        ).order_by('ProjectName')[:20]  # 限制返回20个结果
    else:
        # 如果没有搜索词，返回有权限的前20个项目
        project_queryset = Project.objects.filter(
            ProjectID__in=visible_project_ids
        ).order_by('ProjectName')[:20]
    
    # 格式化结果为JSON格式
    results = []
    for project in project_queryset:
        results.append({
            'id': project.ProjectID,
            'text': project.ProjectName
        })
    
    return JsonResponse({'results': results})

@login_required
def search_tasks(request):
    """任务模糊搜索API视图"""
    # 获取搜索关键词和可能的项目筛选
    search_term = request.GET.get('term', '')
    project_id = request.GET.get('project_id', '')
    
    # 获取用户有权限查看的任务列表
    task_queryset = Task.objects.all()
    task_queryset = filter_queryset_by_role(task_queryset, request.user, "task")
    
    # 应用项目筛选
    if project_id:
        task_queryset = task_queryset.filter(project_id=project_id)
    
    # 应用搜索条件
    if search_term:
        task_queryset = task_queryset.filter(name__icontains=search_term)
    
    # 限制结果数量
    task_queryset = task_queryset.order_by('name')[:20]
    
    # 格式化结果为JSON格式
    results = []
    for task in task_queryset:
        results.append({
            'id': str(task.id),
            'text': task.name
        })
    
    return JsonResponse({'results': results})

@login_required
def update_return_flow(request, consumption_id):
    """直接更新消耗记录的回流值"""
    consumption = get_object_or_404(TaskConsumption, id=consumption_id)
    
    # 检查用户权限
    if not check_task_consumption_permission(request.user, consumption.task, "edit"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': '您没有权限编辑此消耗记录'
            }, status=403)
        
        return render(request, 'consumption_stats/error.html', {
            'error_message': '您没有权限编辑此消耗记录'
        }, status=403)
    
    if request.method == 'POST':
        try:
            # 解析JSON数据
            data = json.loads(request.body)
            new_return_flow = Decimal(data.get('return_flow', 0))
            
            # 更新回流值
            consumption.return_flow = new_return_flow
            consumption.save()  # 这会触发模型中的save方法自动计算其他派生字段
            
            # 返回更新后的数据，格式化为两位小数
            return JsonResponse({
                'success': True,
                'consumption': {
                    'id': str(consumption.id),
                    'return_flow': '{:.2f}'.format(float(consumption.return_flow)),
                    'actual_consumption': '{:.2f}'.format(float(consumption.actual_consumption)),
                    'return_flow_ratio': '{:.2f}'.format(float(consumption.return_flow_ratio)),
                    'registration_cost': '{:.2f}'.format(float(consumption.registration_cost)),
                    'first_deposit_cost': '{:.2f}'.format(float(consumption.first_deposit_cost)),
                    'click_cost': '{:.2f}'.format(float(consumption.click_cost)),
                    'ecpm': '{:.2f}'.format(float(consumption.ecpm))
                }
            })
        
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': f'数据格式错误: {str(e)}'
            }, status=400)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'更新失败: {str(e)}'
            }, status=500)
            
    # 如果不是POST请求，返回405 Method Not Allowed
    return JsonResponse({
        'success': False, 
        'error': '仅支持POST请求'
    }, status=405)
