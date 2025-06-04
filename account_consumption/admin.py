from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .models import AccountConsumption, MonthlyConsumption
from task_management.permissions import TaskPermission
import json
from decimal import Decimal

class MonthlyConsumptionInline(admin.TabularInline):
    model = MonthlyConsumption
    extra = 0
    fields = ('year', 'month', 'amount', 'remark')
    ordering = ('-year', '-month')
    max_num = 3  # 限制显示最近3个月

@admin.register(MonthlyConsumption)
class MonthlyConsumptionAdmin(admin.ModelAdmin):
    list_display = ('account', 'month_display', 'amount', 'remark', 'created_at')
    list_filter = ('year', 'month')
    search_fields = ('account__card_number', 'account__responsible_person', 'remark')
    raw_id_fields = ('account',)
    date_hierarchy = 'created_at'

@admin.register(AccountConsumption)
class AccountConsumptionAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'responsible_person', 'bm_name', 'account_status', 'card_platform')
    list_filter = ('bm_name', 'account_status', 'card_platform', 'has_limit')
    search_fields = ('card_number', 'responsible_person', 'bm_name', 'account_id', 'serial_number')
    list_per_page = 20
    change_list_template = 'admin/account_consumption/account_card_list.html'
    inlines = [MonthlyConsumptionInline]
    
    fieldsets = (
        ('卡片信息', {
            'fields': ('card_number', 'expiry_date', 'cvc', 'full_info')
        }),
        ('账户信息', {
            'fields': ('responsible_person', 'serial_number', 'bm_name', 'has_limit', 'account_id', 'account_status', 'card_platform')
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get_account_cards_data/', self.admin_site.admin_view(self.get_account_cards_data), name='get_account_cards_data'),
            path('<int:account_id>/add_monthly_consumption/', self.admin_site.admin_view(self.add_monthly_consumption_view), name='add_monthly_consumption'),
            path('save_monthly_consumption/', self.admin_site.admin_view(self.save_monthly_consumption), name='save_monthly_consumption'),
            path('get_recent_consumption/<int:account_id>/', self.admin_site.admin_view(self.get_recent_consumption), name='get_recent_consumption'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """自定义列表视图"""
        extra_context = extra_context or {}
        
        # 添加权限信息到模板上下文
        extra_context['has_change_permission'] = self.has_change_permission(request)
        extra_context['has_view_permission'] = self.has_view_permission(request)
        
        # 获取用户角色信息
        user_groups = [group.name for group in request.user.groups.all()]
        extra_context['user_groups'] = user_groups
        
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        """根据用户角色过滤账户数据"""
        queryset = super().get_queryset(request)
        
        # 使用TaskPermission的角色过滤逻辑
        # 这里我们会根据责任人字段进行过滤，类似于任务中的optimizer字段
        if not request.user.is_authenticated:
            return queryset.none()
        
        # 确保只能看到自己公司的数据
        if hasattr(queryset.model, 'company'):
            queryset = queryset.filter(company=request.user.company)
        
        # 获取用户所属的组（角色）
        user_groups = [group.name for group in request.user.groups.all()]
        
        # 如果是超级管理员，返回所有数据
        if request.user.is_superuser:
            return queryset
        
        # 1. 如果用户是优化师角色
        if '优化师' in user_groups and not any(role in user_groups for role in ['部门主管', '小组长']):
            return queryset.filter(responsible_person=request.user.username).distinct()
        
        # 2. 如果用户是小组长角色
        elif '小组长' in user_groups and '部门主管' not in user_groups:
            try:
                departments = request.user.department.all()
                
                if not departments:
                    return queryset.filter(responsible_person=request.user.username).distinct()
                
                # 获取部门的所有成员的用户名
                team_member_usernames = []
                for dept in departments:
                    members = dept.members.all()
                    member_usernames = [member.username for member in members]
                    team_member_usernames.extend(member_usernames)
                
                # 添加小组长自己的用户名
                team_member_usernames.append(request.user.username)
                team_member_usernames = list(set(team_member_usernames))  # 去重
                
                # 过滤账户：责任人是部门成员的账户
                return queryset.filter(responsible_person__in=team_member_usernames).distinct()
            except Exception as e:
                # 如果出现异常，只返回自己的账户
                return queryset.filter(responsible_person=request.user.username).distinct()
        
        # 3. 如果用户是部门主管角色
        elif '部门主管' in user_groups:
            try:
                from organize.models import Department
                # 获取部门主管管理的部门
                managed_department = request.user.managed_department
                
                if not managed_department:
                    return queryset.filter(responsible_person=request.user.username).distinct()
                
                # 获取当前部门及所有子部门
                dept_ids = [managed_department.department_id]
                
                # 递归获取所有子部门ID
                def get_child_dept_ids(parent_id):
                    children = Department.objects.filter(parent_department_id=parent_id)
                    for child in children:
                        dept_ids.append(child.department_id)
                        get_child_dept_ids(child.department_id)
                
                get_child_dept_ids(managed_department.department_id)
                
                # 获取这些部门的所有成员的用户名
                member_usernames = []
                for dept_id in dept_ids:
                    dept = Department.objects.get(department_id=dept_id)
                    dept_members = [member.username for member in dept.members.all()]
                    member_usernames.extend(dept_members)
                    # 如果有部门负责人，也加入成员列表
                    if dept.manager:
                        member_usernames.append(dept.manager.username)
                
                # 添加部门主管自己的用户名
                member_usernames.append(request.user.username)
                member_usernames = list(set(member_usernames))  # 去重
                
                # 过滤账户：责任人是部门成员的账户
                return queryset.filter(responsible_person__in=member_usernames).distinct()
            except Exception as e:
                # 如果出现异常，只返回自己的账户
                return queryset.filter(responsible_person=request.user.username).distinct()
        
        # 4. 其他角色（如管理员）显示公司内所有账户
        return queryset.distinct()

    def get_account_cards_data(self, request):
        """获取账户卡片数据的API"""
        # 从请求中获取过滤参数
        account_status = request.POST.get('account_status', '')
        card_platform = request.POST.get('card_platform', '')
        has_limit = request.POST.get('has_limit', '')
        
        # 获取新增的查询条件
        card_number = request.POST.get('card_number', '')
        responsible_person = request.POST.get('responsible_person', '')
        account_id = request.POST.get('account_id', '')
        
        # 获取DataTables发送的参数
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        
        # 创建基本查询集 - 使用get_queryset确保应用权限过滤
        queryset = self.get_queryset(request)
        
        # 添加筛选条件
        if account_status:
            queryset = queryset.filter(account_status=account_status)
        if card_platform:
            queryset = queryset.filter(card_platform=card_platform)
        if has_limit:
            queryset = queryset.filter(has_limit=has_limit)
            
        # 添加新增的查询条件
        if card_number:
            queryset = queryset.filter(card_number__icontains=card_number)
        if responsible_person:
            queryset = queryset.filter(responsible_person__icontains=responsible_person)
        if account_id:
            queryset = queryset.filter(account_id__icontains=account_id)
            
        # 添加搜索条件
        if search_value:
            queryset = queryset.filter(
                card_number__icontains=search_value
            ) | queryset.filter(
                responsible_person__icontains=search_value
            ) | queryset.filter(
                bm_name__icontains=search_value
            ) | queryset.filter(
                serial_number__icontains=search_value
            )
        
        # 获取记录总数
        total_records = queryset.count()
        
        # 排序
        order_column = request.POST.get('order[0][column]', '0')
        order_dir = request.POST.get('order[0][dir]', 'desc')
        
        # 根据字段索引获取字段名
        columns = ['card_number', 'expiry_date', 'cvc', 'full_info', 'responsible_person', 
                  'serial_number', 'bm_name', 'has_limit', 'account_id', 'account_status', 'card_platform']
        
        if order_column.isdigit() and int(order_column) < len(columns):
            order_field = columns[int(order_column)]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        
        # 分页
        queryset = queryset[start:start + length]
        
        # 准备响应数据
        data = []
        for item in queryset:
            # 获取最近两个月的消耗数据
            recent_consumptions = MonthlyConsumption.objects.filter(account=item).order_by('-year', '-month')[:2]
            recent_consumption_data = []
            
            for consumption in recent_consumptions:
                recent_consumption_data.append({
                    'year': consumption.year,
                    'month': consumption.month,
                    'month_display': consumption.month_display,
                    'amount': str(consumption.amount),
                    'remark': consumption.remark or ''
                })
            
            data.append({
                'id': item.id,
                'card_number': item.card_number,
                'expiry_date': item.expiry_date,
                'cvc': item.cvc,
                'full_info': item.full_info,
                'responsible_person': item.responsible_person,
                'serial_number': item.serial_number,
                'bm_name': item.bm_name,
                'has_limit': item.has_limit,
                'account_id': item.account_id,
                'account_status': item.account_status,
                'card_platform': item.card_platform,
                'recent_consumptions': recent_consumption_data
            })
        
        # 返回JSON响应
        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        }, safe=False)
    
    def add_monthly_consumption_view(self, request, account_id):
        """月度消耗添加表单视图"""
        account = get_object_or_404(AccountConsumption, id=account_id)
        
        # 处理POST请求 - 直接表单提交方式
        if request.method == 'POST' and 'submit_form' in request.POST:
            try:
                year = int(request.POST.get('year'))
                month = int(request.POST.get('month'))
                amount = Decimal(request.POST.get('amount', 0))
                remark = request.POST.get('remark', '')
                
                if amount <= 0:
                    messages.error(request, '消耗金额必须大于0')
                else:
                    # 保存或更新消耗记录
                    obj, created = MonthlyConsumption.objects.update_or_create(
                        account=account,
                        year=year,
                        month=month,
                        defaults={
                            'amount': amount,
                            'remark': remark
                        }
                    )
                    
                    action = "创建" if created else "更新"
                    messages.success(request, f'成功{action}了{year}年{month}月的消耗记录')
                    
                    # 重定向到列表页
                    return HttpResponseRedirect(
                        reverse('admin:account_consumption_accountconsumption_changelist')
                    )
            except Exception as e:
                messages.error(request, f'保存失败: {str(e)}')
        
        # 获取当前年月作为默认值
        current_date = timezone.now()
        default_year = current_date.year
        default_month = current_date.month
        
        # 检查是否已存在本月记录
        existing_record = MonthlyConsumption.objects.filter(
            account=account,
            year=default_year,
            month=default_month
        ).first()
        
        # 获取最近两个月的消耗记录
        recent_consumptions = MonthlyConsumption.objects.filter(
            account=account
        ).order_by('-year', '-month')[:2]
        
        context = {
            'title': f'添加月度消耗 - {account.card_number}',
            'account': account,
            'default_year': default_year,
            'default_month': default_month,
            'existing_record': existing_record,
            'recent_consumptions': recent_consumptions,
            'opts': self.model._meta,
            'has_change_permission': True,  # 允许所有用户都能使用添加消耗功能
            'has_view_permission': True,
        }
        
        return render(request, 'admin/account_consumption/add_monthly_consumption.html', context)
    
    def save_monthly_consumption(self, request):
        """保存月度消耗数据"""
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': '请求方法不允许'})
        
        try:
            # 打印请求数据，便于调试
            print(f"正在处理月度消耗保存请求，POST数据: {request.POST}")
            
            account_id = request.POST.get('account_id')
            year = int(request.POST.get('year'))
            month = int(request.POST.get('month'))
            amount = Decimal(request.POST.get('amount', 0))
            remark = request.POST.get('remark', '')
            
            # 验证输入数据
            if not account_id:
                return JsonResponse({'status': 'error', 'message': '账户ID不能为空'})
            if not year or year < 2000 or year > 2100:
                return JsonResponse({'status': 'error', 'message': '年份不合法'})
            if not month or month < 1 or month > 12:
                return JsonResponse({'status': 'error', 'message': '月份不合法'})
            if amount <= 0:
                return JsonResponse({'status': 'error', 'message': '消耗金额必须大于0'})
            
            # 查找账户，不检查权限
            account = get_object_or_404(AccountConsumption, id=account_id)
            print(f"找到账户: {account.card_number} - {account.responsible_person}")
            
            # 检查是否已存在该月份记录，存在则更新，不存在则创建
            try:
                obj, created = MonthlyConsumption.objects.update_or_create(
                    account=account,
                    year=year,
                    month=month,
                    defaults={
                        'amount': amount,
                        'remark': remark
                    }
                )
                
                action = "创建" if created else "更新"
                print(f"成功{action}消耗记录: {year}年{month}月, 金额: {amount}")
                
                # 获取最近两个月的消耗记录
                recent_consumptions = MonthlyConsumption.objects.filter(
                    account=account
                ).order_by('-year', '-month')[:2]
                
                recent_data = []
                for consumption in recent_consumptions:
                    recent_data.append({
                        'year': consumption.year,
                        'month': consumption.month,
                        'month_display': consumption.month_display,
                        'amount': str(consumption.amount),
                        'remark': consumption.remark or ''
                    })
                
                # 记录成功信息
                messages.success(request, f"已成功{action}{year}年{month}月的消耗记录")
                
                return JsonResponse({
                    'status': 'success', 
                    'message': f'月度消耗数据已成功{action}',
                    'created': created,
                    'recent_data': recent_data,
                    'record': {
                        'year': year,
                        'month': month,
                        'amount': str(amount),
                        'remark': remark
                    }
                })
            except Exception as db_error:
                print(f"数据库操作错误: {str(db_error)}")
                return JsonResponse({'status': 'error', 'message': f'数据库错误: {str(db_error)}'})
            
        except ValueError as ve:
            print(f"值错误: {str(ve)}")
            return JsonResponse({'status': 'error', 'message': f'输入值不合法: {str(ve)}'})
        except Exception as e:
            print(f"保存消耗记录时发生错误: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'保存失败: {str(e)}'})
    
    def get_recent_consumption(self, request, account_id):
        """获取最近的消耗数据"""
        try:
            # 不检查权限，允许所有用户访问
            account = get_object_or_404(AccountConsumption, id=account_id)
            recent_consumptions = MonthlyConsumption.objects.filter(
                account=account
            ).order_by('-year', '-month')[:2]
            
            data = []
            for consumption in recent_consumptions:
                data.append({
                    'id': consumption.id,
                    'year': consumption.year,
                    'month': consumption.month,
                    'month_display': consumption.month_display,
                    'amount': str(consumption.amount),
                    'remark': consumption.remark or ''
                })
            
            return JsonResponse({'status': 'success', 'data': data})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
