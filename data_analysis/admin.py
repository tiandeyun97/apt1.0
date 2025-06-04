from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from consumption_management.models import TaskConsumption
from datetime import datetime, timedelta, date
from django.db.models import Sum, Avg, F, Q, Count
from django.http import JsonResponse
import json
from .models import ConsumptionAnalysis, OptimizerRanking
from organize.models import User
from task_management.models import Task
from tasks.models import Project
from organize.models import Department

@admin.register(ConsumptionAnalysis)
class ConsumptionAnalysisAdmin(admin.ModelAdmin):
    """消费数据分析管理模块"""
    change_list_template = 'admin/data_analysis/consumption_trend.html'
    
    def has_module_permission(self, request):
        """是否有权查看此模块"""
        user = request.user
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=['管理员', '运营']).exists()
    
    def has_view_permission(self, request, obj=None):
        """是否有权查看数据"""
        user = request.user
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=['管理员', '运营']).exists()
    
    def has_add_permission(self, request):
        """是否有权添加数据"""
        return False  # 不允许添加数据
    
    def has_change_permission(self, request, obj=None):
        """是否有权修改数据"""
        return False  # 不允许修改数据
    
    def has_delete_permission(self, request, obj=None):
        """是否有权删除数据"""
        return False  # 不允许删除数据
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get_consumption_data/', self.admin_site.admin_view(self.get_consumption_data), name='get_consumption_data'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_consumption_data(self, request):
        """获取消费趋势数据"""
        today = datetime.now().date()
        
        # 检查是否有自定义日期范围请求
        period = request.GET.get('period', '')
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', '')
        
        # 处理自定义日期范围请求
        if period == 'custom' and start_date_str and end_date_str:
            try:
                # 解析日期
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                
                # 检查日期范围是否合法
                if start_date > end_date:
                    return JsonResponse({'error': '开始日期不能晚于结束日期'}, status=400)
                
                # 检查日期范围是否超过限制 (62天)
                date_diff = (end_date - start_date).days
                if date_diff > 62:
                    return JsonResponse({'error': '日期范围不能超过62天'}, status=400)
                
                # 获取自定义日期范围的数据
                custom_data = self._get_daily_consumption(start_date, end_date)
                
                # 确保数据非空
                if not custom_data:
                    custom_data = [self._create_empty_data_item(start_date)]
                
                # 计算总计值
                custom_total = self._calculate_totals(custom_data)
                
                # 返回自定义数据
                return JsonResponse({
                    'custom_data': custom_data,
                    'custom_total': custom_total
                }, safe=True)
                
            except ValueError:
                return JsonResponse({'error': '日期格式无效'}, status=400)
        
        # 以下是原有逻辑
        # 本周数据 (从周一开始到今天)
        week_start = today - timedelta(days=today.weekday())
        week_data = self._get_daily_consumption(week_start, today)
        
        # 本月数据
        month_start = today.replace(day=1)
        month_data = self._get_daily_consumption(month_start, today)
        
        # 获取当年每月数据
        current_year = today.year
        yearly_data = self._get_monthly_consumption(current_year)
        
        # 确保数据非空，如果没有数据则创建默认数据
        if not week_data:
            week_data = [self._create_empty_data_item(week_start)]
        
        if not month_data:
            month_data = [self._create_empty_data_item(month_start)]
        
        if not yearly_data:
            yearly_data = [self._create_empty_data_item(date(current_year, 1, 1))]
        
        # 计算各类型消费的总额
        week_total = self._calculate_totals(week_data)
        month_total = self._calculate_totals(month_data)
        yearly_total = self._calculate_totals(yearly_data)
        
        return JsonResponse({
            'week_data': week_data,
            'month_data': month_data,
            'yearly_data': yearly_data,
            'week_total': week_total,
            'month_total': month_total,
            'yearly_total': yearly_total
        }, safe=True)
    
    def _create_empty_total(self):
        """创建空的总计数据"""
        return {
            'total_consumption': 0,
            'total_return_flow': 0,
            'total_actual_consumption': 0,
            'avg_registration_cost': 0,
            'avg_first_deposit_cost': 0
        }
    
    def _create_empty_data_item(self, date):
        """创建空的数据项，用于没有数据时显示"""
        return {
            'date': date.strftime('%Y-%m-%d'),
            'total_consumption': 0,
            'total_return_flow': 0,
            'total_actual_consumption': 0,
            'avg_registration_cost': 0,
            'avg_first_deposit_cost': 0
        }
    
    def _get_monthly_consumption(self, year):
        """获取指定年份的每月消费数据"""
        from django.db.models.functions import TruncMonth
        
        # 设置日期范围
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # 按月分组查询
        queryset = TaskConsumption.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_consumption=Sum('daily_consumption'),
            total_return_flow=Sum('return_flow'),
            total_actual_consumption=Sum('actual_consumption'),
            avg_registration_cost=Avg('registration_cost'),
            avg_first_deposit_cost=Avg('first_deposit_cost')
        ).order_by('month')
        
        # 转换为前端需要的格式
        result = []
        for item in queryset:
            result.append({
                'date': item['month'].strftime('%Y-%m-%d'),
                'total_consumption': float(item['total_consumption']) if item['total_consumption'] else 0,
                'total_return_flow': float(item['total_return_flow']) if item['total_return_flow'] else 0,
                'total_actual_consumption': float(item['total_actual_consumption']) if item['total_actual_consumption'] else 0,
                'avg_registration_cost': float(item['avg_registration_cost']) if item['avg_registration_cost'] else 0,
                'avg_first_deposit_cost': float(item['avg_first_deposit_cost']) if item['avg_first_deposit_cost'] else 0
            })
        return result
    
    def _get_daily_consumption(self, start_date, end_date):
        """获取指定日期范围内的日消费数据"""
        queryset = TaskConsumption.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).values('date').annotate(
            total_consumption=Sum('daily_consumption'),
            total_return_flow=Sum('return_flow'),
            total_actual_consumption=Sum('actual_consumption'),
            avg_registration_cost=Avg('registration_cost'),
            avg_first_deposit_cost=Avg('first_deposit_cost')
        ).order_by('date')
        
        # 转换为前端需要的格式
        result = []
        for item in queryset:
            result.append({
                'date': item['date'].strftime('%Y-%m-%d'),
                'total_consumption': float(item['total_consumption']) if item['total_consumption'] else 0,
                'total_return_flow': float(item['total_return_flow']) if item['total_return_flow'] else 0,
                'total_actual_consumption': float(item['total_actual_consumption']) if item['total_actual_consumption'] else 0,
                'avg_registration_cost': float(item['avg_registration_cost']) if item['avg_registration_cost'] else 0,
                'avg_first_deposit_cost': float(item['avg_first_deposit_cost']) if item['avg_first_deposit_cost'] else 0
            })
        return result
    
    def _calculate_totals(self, data_list):
        """计算总计值"""
        total_consumption = sum(item['total_consumption'] for item in data_list)
        total_return_flow = sum(item['total_return_flow'] for item in data_list)
        total_actual_consumption = sum(item['total_actual_consumption'] for item in data_list)
        
        # 计算平均值 (避免除零错误)
        if len(data_list) > 0:
            avg_registration_cost = sum(item['avg_registration_cost'] for item in data_list) / len(data_list)
            avg_first_deposit_cost = sum(item['avg_first_deposit_cost'] for item in data_list) / len(data_list)
        else:
            avg_registration_cost = 0
            avg_first_deposit_cost = 0
            
        return {
            'total_consumption': total_consumption,
            'total_return_flow': total_return_flow,
            'total_actual_consumption': total_actual_consumption,
            'avg_registration_cost': avg_registration_cost,
            'avg_first_deposit_cost': avg_first_deposit_cost
        }

@admin.register(OptimizerRanking)
class OptimizerRankingAdmin(admin.ModelAdmin):
    """优化师榜单排名管理模块"""
    change_list_template = 'admin/data_analysis/optimizer_ranking.html'
    
    def has_module_permission(self, request):
        """是否有权查看此模块"""
        user = request.user
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=['管理员', '运营']).exists()
    
    def has_view_permission(self, request, obj=None):
        """是否有权查看数据"""
        user = request.user
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=['管理员', '运营']).exists()
    
    def has_add_permission(self, request):
        """是否有权添加数据"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """是否有权修改数据"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """是否有权删除数据"""
        return False
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get_ranking_data/', self.admin_site.admin_view(self.get_ranking_data), name='get_ranking_data'),
            path('search_projects/', self.admin_site.admin_view(self.search_projects), name='search_projects'),
            path('search_departments/', self.admin_site.admin_view(self.search_departments), name='search_departments'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        return super().changelist_view(request, extra_context=extra_context)
    
    def search_projects(self, request):
        """项目模糊搜索API视图"""
        keyword = request.GET.get('keyword', '')
        
        # 如果搜索关键词太短，返回空结果
        if len(keyword) < 2:
            return JsonResponse({'projects': []})
        
        # 使用模糊查询搜索项目
        projects = Project.objects.filter(
            ProjectName__icontains=keyword
        ).select_related('MediaChannelID', 'TaskTypeID').order_by('ProjectName')[:10]  # 限制返回10个结果
        
        # 格式化结果为JSON
        result = [
            {
                'id': project.ProjectID,
                'name': project.ProjectName,
                'media_channel': project.MediaChannelID.MediaChannelName if project.MediaChannelID else '无',
                'task_type': project.TaskTypeID.TaskTypeName if project.TaskTypeID else '无'
            } for project in projects
        ]
        
        return JsonResponse({'projects': result})
    
    def search_departments(self, request):
        """部门搜索API视图"""
        keyword = request.GET.get('keyword', '')
        
        # 获取所有部门（按状态为正常的部门）
        departments = Department.objects.filter(
            status='normal',
            company=request.user.company
        ).order_by('department_name')
        
        # 如果有搜索关键词，进行过滤
        if keyword:
            departments = departments.filter(department_name__icontains=keyword)
        
        # 格式化结果为JSON
        result = []
        for dept in departments:
            # 获取部门成员数量
            member_count = dept.members.count()
            
            result.append({
                'id': str(dept.department_id),
                'name': dept.department_name,
                'code': dept.department_code,
                'member_count': member_count,
                'manager_name': dept.manager.username if dept.manager else '未设置'
            })
        
        return JsonResponse({'departments': result})
    
    def get_ranking_data(self, request):
        """获取优化师排名数据"""
        # 获取请求中的参数
        period = request.GET.get('period', 'daily')
        target_date_str = request.GET.get('date', None)
        start_date_str = request.GET.get('start_date', None)
        end_date_str = request.GET.get('end_date', None)
        project_id = request.GET.get('project_id', None)
        department_id = request.GET.get('department_id', None)
        
        # 如果是项目排名，则获取项目下优化师的排名数据
        if period == 'project' and project_id:
            return self._get_project_ranking(project_id)
        
        # 如果是部门排名，则获取部门下优化师的排名数据
        if period == 'department' and department_id:
            return self._get_department_ranking(department_id, start_date_str, end_date_str)
        
        # 处理日期参数
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 计算周起止日期
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # 计算月起止日期
        month_start = date(today.year, today.month, 1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        # 解析目标日期
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = yesterday
        else:
            target_date = yesterday
            
        # 解析开始日期和结束日期
        custom_start_date = None
        custom_end_date = None
        
        if start_date_str:
            try:
                custom_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                custom_start_date = month_start
                
        if end_date_str:
            try:
                custom_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                custom_end_date = month_end
                
        # 根据周期获取数据
        ranking_data = []
        
        if period == 'daily':
            # 返回每日排名数据
            ranking_data = self._get_daily_ranking(target_date, department_id)
        elif period == 'weekly':
            # 返回周排名数据
            ranking_data = self._get_period_ranking(week_start, week_end, department_id)
        elif period == 'monthly':
            # 返回月排名数据
            if custom_start_date and custom_end_date:
                month_start = custom_start_date
                month_end = custom_end_date
            ranking_data = self._get_period_ranking(month_start, month_end, department_id)
        else:
            # 默认返回昨日数据
            ranking_data = self._get_daily_ranking(yesterday, department_id)
        
        # 构建返回数据
        result = {
            'ranking_data': ranking_data,
            'period': period,
            'date_info': {
                'start_date': month_start.strftime('%Y-%m-%d') if period == 'monthly' else week_start.strftime('%Y-%m-%d') if period == 'weekly' else target_date.strftime('%Y-%m-%d'),
                'end_date': month_end.strftime('%Y-%m-%d') if period == 'monthly' else week_end.strftime('%Y-%m-%d') if period == 'weekly' else target_date.strftime('%Y-%m-%d'),
                'today': today.strftime('%Y-%m-%d'),
                'yesterday': yesterday.strftime('%Y-%m-%d')
            }
        }
        
        # 如果指定了部门，添加部门信息
        if department_id:
            try:
                department = Department.objects.get(department_id=department_id)
                result['department_info'] = {
                    'id': str(department.department_id),
                    'name': department.department_name,
                    'code': department.department_code
                }
            except Department.DoesNotExist:
                pass
        
        return JsonResponse(result, safe=True)
    
    def _get_project_ranking(self, project_id):
        """获取项目下优化师的排名数据"""
        try:
            # 获取项目信息
            project = Project.objects.get(ProjectID=project_id)
            
            # 获取项目下的所有任务
            tasks = Task.objects.filter(project_id=project_id)
            
            if not tasks.exists():
                return JsonResponse({
                    'ranking_data': [],
                    'period': 'project',
                    'project_info': {
                        'id': project.ProjectID, 
                        'name': project.ProjectName
                    }
                })
            
            # 获取这些任务下的消耗数据，按优化师分组
            task_ids = tasks.values_list('id', flat=True)
            
            queryset = TaskConsumption.objects.filter(
                task_id__in=task_ids
            ).values(
                'creator'
            ).annotate(
                total_consumption=Sum('daily_consumption'),
                total_return_flow=Sum('return_flow'),
                total_actual_consumption=Sum('actual_consumption'),
                task_count=Count('task', distinct=True)
            ).order_by('-total_actual_consumption')
            
            # 格式化排名数据
            ranking_data = self._format_ranking_data(queryset)
            
            # 构建返回数据
            result = {
                'ranking_data': ranking_data,
                'period': 'project',
                'project_info': {
                    'id': project.ProjectID, 
                    'name': project.ProjectName
                }
            }
            
            return JsonResponse(result, safe=True)
            
        except Project.DoesNotExist:
            return JsonResponse({
                'ranking_data': [],
                'period': 'project',
                'project_info': {
                    'id': None, 
                    'name': '项目不存在'
                }
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'ranking_data': [],
                'period': 'project'
            })
    
    def _get_daily_ranking(self, date, department_id=None):
        """获取指定日期的优化师排名数据"""
        # 基础过滤条件
        filter_conditions = {'date': date}
        
        # 如果指定了部门，获取部门成员ID列表
        if department_id:
            try:
                department = Department.objects.get(department_id=department_id)
                
                # 获取部门所有成员ID
                member_ids = list(department.members.all().values_list('id', flat=True))
                
                # 添加部门主管ID（如果存在）
                if department.manager and department.manager.id not in member_ids:
                    member_ids.append(department.manager.id)
                    
                if member_ids:
                    filter_conditions['creator_id__in'] = member_ids
            except Department.DoesNotExist:
                pass
        
        # 按优化师(创建人)分组，计算该日期的总消耗
        queryset = TaskConsumption.objects.filter(**filter_conditions).values(
            'creator'
        ).annotate(
            total_consumption=Sum('daily_consumption'),
            total_return_flow=Sum('return_flow'),
            total_actual_consumption=Sum('actual_consumption'),
            task_count=Count('task', distinct=True)
        ).order_by('-total_actual_consumption')
        
        # 获取用户信息
        return self._format_ranking_data(queryset)
    
    def _get_period_ranking(self, start_date, end_date, department_id=None):
        """获取指定时间段的优化师排名数据"""
        # 基础过滤条件
        filter_conditions = {
            'date__gte': start_date,
            'date__lte': end_date
        }
        
        # 如果指定了部门，获取部门成员ID列表
        if department_id:
            try:
                department = Department.objects.get(department_id=department_id)
                
                # 获取部门所有成员ID
                member_ids = list(department.members.all().values_list('id', flat=True))
                
                # 添加部门主管ID（如果存在）
                if department.manager and department.manager.id not in member_ids:
                    member_ids.append(department.manager.id)
                    
                if member_ids:
                    filter_conditions['creator_id__in'] = member_ids
            except Department.DoesNotExist:
                pass
        
        # 按优化师(创建人)分组，计算该时间段的总消耗
        queryset = TaskConsumption.objects.filter(**filter_conditions).values(
            'creator'
        ).annotate(
            total_consumption=Sum('daily_consumption'),
            total_return_flow=Sum('return_flow'),
            total_actual_consumption=Sum('actual_consumption'),
            task_count=Count('task', distinct=True)
        ).order_by('-total_actual_consumption')
        
        # 获取用户信息
        return self._format_ranking_data(queryset)
    
    def _format_ranking_data(self, queryset):
        """格式化排名数据，添加用户信息"""
        result = []
        rank = 1
        
        # 用户ID到用户对象的映射
        user_ids = [item['creator'] for item in queryset if item['creator']]
        user_map = {user.id: user for user in User.objects.filter(id__in=user_ids)}
        
        # 获取所有相关部门的主管信息
        department_ids = set()
        for user_id, user in user_map.items():
            if hasattr(user, 'department') and user.department.exists():
                # 用户可能属于多个部门，我们取第一个部门
                first_dept = user.department.first()
                if first_dept:
                    department_ids.add(first_dept.department_id)
        
        # 创建部门主管映射
        dept_manager_map = {}
        for dept in Department.objects.filter(department_id__in=department_ids):
            if dept.manager:
                dept_manager_map[dept.department_id] = dept.manager.id
        
        # 格式化结果
        for item in queryset:
            # 获取用户信息
            user_id = item['creator']
            if not user_id or user_id not in user_map:
                continue
                
            user = user_map[user_id]
            
            # 判断用户是否为部门主管
            is_manager = False
            user_dept = None
            dept_id = None
            
            # 获取用户的第一个部门
            if hasattr(user, 'department') and user.department.exists():
                user_dept = user.department.first()
                dept_id = user_dept.department_id if user_dept else None
                
                # 检查用户是否是该部门的主管
                if dept_id and dept_id in dept_manager_map and dept_manager_map[dept_id] == user.id:
                    is_manager = True
            
            # 创建排名项
            ranking_item = {
                'rank': rank,
                'username': user.username,
                'nickname': user.nickname if hasattr(user, 'nickname') and user.nickname else user.username,
                'department': user_dept.department_name if user_dept else '未分配',
                'department_id': str(dept_id) if dept_id else None,
                'is_manager': is_manager,
                'total_consumption': float(item['total_consumption']),
                'total_return_flow': float(item['total_return_flow']),
                'total_actual_consumption': float(item['total_actual_consumption']),
                'task_count': item['task_count']
            }
            
            # 添加到结果列表
            result.append(ranking_item)
            rank += 1
        
        return result
    
    def _get_department_ranking(self, department_id, start_date_str=None, end_date_str=None):
        """获取部门下优化师的排名数据"""
        try:
            # 获取部门信息
            department = Department.objects.get(department_id=department_id)
            
            # 获取部门成员ID列表
            member_ids = list(department.members.all().values_list('id', flat=True))
            
            # 添加部门主管ID（如果存在）
            if department.manager and department.manager.id not in member_ids:
                member_ids.append(department.manager.id)
            
            if not member_ids:
                return JsonResponse({
                    'ranking_data': [],
                    'period': 'department',
                    'department_info': {
                        'id': str(department.department_id),
                        'name': department.department_name,
                        'code': department.department_code
                    }
                })
            
            # 处理日期范围
            today = date.today()
            month_start = date(today.year, today.month, 1)
            if today.month == 12:
                month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
            
            # 解析日期范围
            start_date = month_start
            end_date = month_end
            
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
                    
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            # 获取部门成员的消耗数据
            queryset = TaskConsumption.objects.filter(
                creator_id__in=member_ids,
                date__gte=start_date,
                date__lte=end_date
            ).values(
                'creator'
            ).annotate(
                total_consumption=Sum('daily_consumption'),
                total_return_flow=Sum('return_flow'),
                total_actual_consumption=Sum('actual_consumption'),
                task_count=Count('task', distinct=True)
            ).order_by('-total_actual_consumption')
            
            # 格式化排名数据
            ranking_data = self._format_ranking_data(queryset)
            
            # 计算部门总数据
            department_stats = {
                'total_consumption': sum(item['total_consumption'] for item in ranking_data),
                'total_actual_consumption': sum(item['total_actual_consumption'] for item in ranking_data),
                'optimizer_count': len(ranking_data),
                'task_count': sum(item['task_count'] for item in ranking_data)
            }
            
            # 构建返回数据
            result = {
                'ranking_data': ranking_data,
                'period': 'department',
                'department_info': {
                    'id': str(department.department_id),
                    'name': department.department_name,
                    'code': department.department_code
                },
                'date_info': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                },
                'department_stats': department_stats
            }
            
            return JsonResponse(result, safe=True)
            
        except Department.DoesNotExist:
            return JsonResponse({
                'ranking_data': [],
                'period': 'department',
                'department_info': {
                    'id': None,
                    'name': '部门不存在'
                }
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'ranking_data': [],
                'period': 'department'
            })
