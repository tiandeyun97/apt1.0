from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Case, When, Value, IntegerField, F, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages
import datetime
import json
import calendar
import csv
import os
from decimal import Decimal
import decimal
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.db import models
import uuid

from .models import ReconciliationRecord, ReconciliationHistory, ReconciliationAttachment
from task_management.models import Task
from tasks.models import Project

# 首页视图 - 重定向到等待对账
@login_required
def index(request):
    return redirect('reconciliation:waiting_list')

# 等待对账列表视图
@login_required
def waiting_list(request):
    # 检查是否在admin界面
    is_admin = '/admin/' in request.path
    
    # 获取当前日期
    today = timezone.now()
    
    # 获取可用年份和月份列表
    available_years_months = ReconciliationRecord.objects.values('year', 'month').distinct().order_by('-year', '-month')
    
    # 如果没有可用的年月数据，使用当前年月
    if not available_years_months:
        default_year = today.year
        default_month = today.month
    else:
        # 默认显示最新的年月数据
        default_year = available_years_months[0]['year']
        default_month = available_years_months[0]['month']
    
    # 从查询参数获取年月，如果没有则使用默认值
    current_year = int(request.GET.get('year', default_year))
    current_month = int(request.GET.get('month', default_month))
    
    # 构建基础查询
    records = ReconciliationRecord.objects.filter(
        status='waiting'
    ).select_related('project', 'task').prefetch_related('task__optimizer')
    
    # 按年月过滤
    records = records.filter(year=current_year, month=current_month)
    
    # 处理搜索和过滤
    project_id = request.GET.get('project')
    search_query = request.GET.get('search', '')
    
    if project_id:
        records = records.filter(project_id=project_id)
    
    if search_query:
        records = records.filter(
            Q(task__name__icontains=search_query) | 
            Q(project__ProjectName__icontains=search_query)
        )
    
    # 排序
    sort_by = request.GET.get('sort_by', 'project')
    if sort_by == 'project':
        records = records.order_by('project__ProjectName', 'task__name')
    elif sort_by == 'task':
        records = records.order_by('task__name')
    elif sort_by == 'consumption':
        records = records.order_by('-actual_consumption')
    
    # 分页
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取当前年月下有等待对账记录的项目列表
    available_projects = Project.objects.filter(
        reconciliation_records__year=current_year,
        reconciliation_records__month=current_month,
        reconciliation_records__status='waiting'
    ).distinct().order_by('ProjectName')
    
    # 确保当前年份在年份列表中
    available_years = sorted(set([ym['year'] for ym in available_years_months] + [today.year]), reverse=True)
    
    context = {
        'active_page': 'waiting',
        'records': page_obj,
        'projects': available_projects,
        'current_project': project_id,
        'search_query': search_query,
        'sort_by': sort_by,
        'current_year': current_year,
        'current_month': current_month,
        'available_years_months': available_years_months,
        'years': available_years,
        'is_admin': is_admin,
    }
    
    return render(request, 'reconciliation_management/waiting_list.html', context)

# 异常对账列表视图
@login_required
def exception_list(request):
    # 检查是否在admin界面
    is_admin = '/admin/' in request.path
    
    # 获取当前日期
    today = timezone.now()
    
    # 获取可用年份和月份列表
    available_years_months = ReconciliationRecord.objects.values('year', 'month').distinct().order_by('-year', '-month')
    
    # 如果没有可用的年月数据，使用当前年月
    if not available_years_months:
        default_year = today.year
        default_month = today.month
    else:
        # 默认显示最新的年月数据
        default_year = available_years_months[0]['year']
        default_month = available_years_months[0]['month']
    
    # 从查询参数获取年月，如果没有则使用默认值
    current_year = int(request.GET.get('year', default_year))
    current_month = int(request.GET.get('month', default_month))
    
    # 构建基础查询
    records = ReconciliationRecord.objects.filter(
        status='exception'
    ).select_related('project', 'task').prefetch_related('task__optimizer')
    
    # 按年月过滤
    records = records.filter(year=current_year, month=current_month)
    
    # 处理搜索和过滤
    project_id = request.GET.get('project')
    search_query = request.GET.get('search', '')
    
    if project_id:
        records = records.filter(project_id=project_id)
    
    if search_query:
        records = records.filter(
            Q(task__name__icontains=search_query) | 
            Q(project__ProjectName__icontains=search_query)
        )
    
    # 排序
    sort_by = request.GET.get('sort_by', 'project')
    if sort_by == 'project':
        records = records.order_by('project__ProjectName', 'task__name')
    elif sort_by == 'task':
        records = records.order_by('task__name')
    elif sort_by == 'consumption':
        records = records.order_by('-actual_consumption')
    elif sort_by == 'difference':
        records = records.order_by('-difference_percentage')
    
    # 分页
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取当前年月下有异常对账记录的项目列表
    available_projects = Project.objects.filter(
        reconciliation_records__year=current_year,
        reconciliation_records__month=current_month,
        reconciliation_records__status='exception'
    ).distinct().order_by('ProjectName')
    
    # 确保当前年份在年份列表中
    available_years = sorted(set([ym['year'] for ym in available_years_months] + [today.year]), reverse=True)
    
    context = {
        'active_page': 'exception',
        'records': page_obj,
        'projects': available_projects,
        'current_project': project_id,
        'search_query': search_query,
        'sort_by': sort_by,
        'current_year': current_year,
        'current_month': current_month,
        'available_years_months': available_years_months,
        'years': available_years,
        'is_admin': is_admin,
    }
    
    return render(request, 'reconciliation_management/exception_list.html', context)

# 完成对账列表视图
@login_required
def completed_list(request):
    # 检查是否在admin界面
    is_admin = '/admin/' in request.path
    
    # 获取当前日期
    today = timezone.now()
    
    # 获取可用年份和月份列表
    available_years_months = ReconciliationRecord.objects.values('year', 'month').distinct().order_by('-year', '-month')
    
    # 如果没有可用的年月数据，使用当前年月
    if not available_years_months:
        default_year = today.year
        default_month = today.month
    else:
        # 默认显示最新的年月数据
        default_year = available_years_months[0]['year']
        default_month = available_years_months[0]['month']
    
    # 从查询参数获取年月，如果没有则使用默认值
    current_year = int(request.GET.get('year', default_year))
    current_month = int(request.GET.get('month', default_month))
    
    # 构建基础查询
    records = ReconciliationRecord.objects.filter(
        status='completed'
    ).select_related('project', 'task').prefetch_related('task__optimizer')
    
    # 按年月过滤
    records = records.filter(year=current_year, month=current_month)
    
    # 处理搜索和过滤
    project_id = request.GET.get('project')
    search_query = request.GET.get('search', '')
    
    if project_id:
        records = records.filter(project_id=project_id)
    
    if search_query:
        records = records.filter(
            Q(task__name__icontains=search_query) | 
            Q(project__ProjectName__icontains=search_query)
        )
    
    # 排序
    sort_by = request.GET.get('sort_by', 'project')
    if sort_by == 'project':
        records = records.order_by('project__ProjectName', 'task__name')
    elif sort_by == 'task':
        records = records.order_by('task__name')
    elif sort_by == 'consumption':
        records = records.order_by('-actual_consumption')
    elif sort_by == 'difference':
        records = records.order_by('-difference_percentage')
    
    # 分页
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取当前年月下有完成对账记录的项目列表
    available_projects = Project.objects.filter(
        reconciliation_records__year=current_year,
        reconciliation_records__month=current_month,
        reconciliation_records__status='completed'
    ).distinct().order_by('ProjectName')
    
    # 确保当前年份在年份列表中
    available_years = sorted(set([ym['year'] for ym in available_years_months] + [today.year]), reverse=True)
    
    context = {
        'active_page': 'completed',
        'records': page_obj,
        'projects': available_projects,
        'current_project': project_id,
        'search_query': search_query,
        'sort_by': sort_by,
        'current_year': current_year,
        'current_month': current_month,
        'available_years_months': available_years_months,
        'years': available_years,
        'is_admin': is_admin,
    }
    
    return render(request, 'reconciliation_management/completed_list.html', context)

# 对账记录详情视图
@login_required
def record_detail(request, record_id):
    record = get_object_or_404(ReconciliationRecord, id=record_id)
    
    # 获取历史记录
    histories = record.histories.order_by('-operated_at')
    
    # 获取附件
    attachments = record.attachments.order_by('-uploaded_at')
    
    # 如果是AJAX请求，返回JSON响应
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 构建响应数据
        record_data = {
            'id': str(record.id),
            'year': record.year,
            'month': record.month,
            'project_id': str(record.project_id),
            'project_name': record.project.ProjectName,
            'task_id': str(record.task_id),
            'task_name': record.task.name,
            'actual_consumption': str(record.actual_consumption),
            'fb_consumption': str(record.fb_consumption) if record.fb_consumption is not None else None,
            'difference': str(record.difference),
            'difference_percentage': str(record.difference_percentage),
            'status': record.status,
            'status_display': record.get_status_display(),
            'is_manually_confirmed': record.is_manually_confirmed,
            'confirmed_by': record.confirmed_by.username if record.confirmed_by else None,
            'confirmed_at': record.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if record.confirmed_at else None,
            'note': record.note,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'record': record_data
        })
    
    context = {
        'record': record,
        'histories': histories,
        'attachments': attachments,
    }
    
    return render(request, 'reconciliation_management/record_detail.html', context)

# 更新FB消耗视图
@login_required
def update_fb_consumption(request, record_id):
    record = get_object_or_404(ReconciliationRecord, id=record_id)
    
    if request.method == 'POST':
        fb_consumption = request.POST.get('fb_consumption')
        note = request.POST.get('note', '')
        attachment_file = request.FILES.get('attachment_file')
        
        try:
            # 将fb_consumption转换为Decimal类型
            fb_consumption = Decimal(fb_consumption)
            old_fb_consumption = record.fb_consumption
            old_status = record.status
            
            record.fb_consumption = fb_consumption
            record.note = note
            record.save()
            
            # 创建历史记录
            history = ReconciliationHistory.objects.create(
                reconciliation=record,
                action='update',
                old_status=old_status,
                new_status=record.status,
                old_fb_consumption=old_fb_consumption,
                new_fb_consumption=record.fb_consumption,
                difference=record.difference,
                note=f"更新FB消耗: {old_fb_consumption} -> {record.fb_consumption}",
                operated_by=request.user
            )
            
            # 处理附件上传
            if attachment_file:
                # 检查文件类型
                if attachment_file.content_type not in ['image/jpeg', 'image/png']:
                    messages.error(request, '附件必须是JPG或PNG格式')
                    return redirect('reconciliation:waiting_list')
                
                # 如果图片太大，进行服务器端压缩
                if attachment_file.size > 1024 * 1024:  # 大于1MB
                    # 打开图片
                    img = Image.open(attachment_file)
                    
                    # 保持宽高比例进行缩放
                    max_size = (1600, 1200)
                    img.thumbnail(max_size, Image.LANCZOS)
                    
                    # 确定输出格式
                    output_format = 'JPEG' if attachment_file.content_type == 'image/jpeg' else 'PNG'
                    
                    # 创建BytesIO对象
                    output = BytesIO()
                    
                    # 保存压缩后的图片
                    img.save(output, format=output_format, quality=75)
                    output.seek(0)
                    
                    # 创建新的InMemoryUploadedFile对象
                    compressed_file = InMemoryUploadedFile(
                        output,
                        'attachment_file',
                        os.path.splitext(attachment_file.name)[0] + ('.jpg' if output_format == 'JPEG' else '.png'),
                        'image/jpeg' if output_format == 'JPEG' else 'image/png',
                        sys.getsizeof(output),
                        None
                    )
                    
                    # 用压缩后的文件替换原文件
                    attachment_file = compressed_file
                
                # 计算文件大小（KB）
                file_size = attachment_file.size // 1024
                
                # 创建附件记录
                attachment = ReconciliationAttachment.objects.create(
                    reconciliation=record,
                    file=attachment_file,
                    file_name=attachment_file.name,
                    file_size=file_size,
                    uploaded_by=request.user
                )
                
                # 更新历史记录，添加附件信息
                history.note += f", 上传附件: {attachment_file.name}"
                history.save()
            
            messages.success(request, '成功更新FB消耗')
            
            # 根据来源页面重定向
            redirect_to = request.POST.get('redirect_to', 'waiting')
            if redirect_to == 'waiting':
                return redirect('reconciliation:waiting_list')
            elif redirect_to == 'exception':
                return redirect('reconciliation:exception_list')
            elif redirect_to == 'completed':
                return redirect('reconciliation:completed_list')
            else:
                return redirect('reconciliation:dashboard')
            
        except (ValueError, decimal.InvalidOperation):
            messages.error(request, 'FB消耗必须是有效的数字')
    
    context = {
        'record': record,
    }
    
    return render(request, 'reconciliation_management/update_fb_consumption.html', context)

# 手动确认对账视图
@login_required
def manual_confirm(request, record_id):
    record = get_object_or_404(ReconciliationRecord, id=record_id)
    
    if request.method == 'POST':
        note = request.POST.get('note', '')
        old_status = record.status
        
        record.manual_confirm(request.user)
        
        if note:
            record.note = note
            record.save()
        
        # 创建历史记录
        ReconciliationHistory.objects.create(
            reconciliation=record,
            action='confirm',
            old_status=old_status,
            new_status='completed',
            old_fb_consumption=record.fb_consumption,
            new_fb_consumption=record.fb_consumption,
            difference=record.difference,
            note=f"手动确认完成对账: {note}",
            operated_by=request.user
        )
        
        # 如果是AJAX请求，返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '成功手动确认对账',
                'record_id': str(record.id),
                'status': record.status,
                'status_display': record.get_status_display()
            })
        
        messages.success(request, '成功手动确认对账')
        return redirect('reconciliation:exception_list')
    
    context = {
        'record': record,
    }
    
    return render(request, 'reconciliation_management/manual_confirm.html', context)

# 上传附件视图
@login_required
def upload_attachment(request, record_id):
    record = get_object_or_404(ReconciliationRecord, id=record_id)
    
    if request.method == 'POST' and request.FILES.get('attachment_file'):
        attachment_file = request.FILES['attachment_file']
        
        # 计算文件大小（KB）
        file_size = attachment_file.size // 1024
        
        # 创建附件记录
        ReconciliationAttachment.objects.create(
            reconciliation=record,
            file=attachment_file,
            file_name=attachment_file.name,
            file_size=file_size,
            uploaded_by=request.user
        )
        
        messages.success(request, '附件上传成功')
        
        # 创建历史记录
        ReconciliationHistory.objects.create(
            reconciliation=record,
            action='update',
            old_status=record.status,
            new_status=record.status,
            note=f"上传附件: {attachment_file.name}",
            operated_by=request.user
        )
        
        return redirect('reconciliation:record_detail', record_id=record.id)
    
    messages.error(request, '上传附件失败')
    return redirect('reconciliation:record_detail', record_id=record.id)

# 导出对账数据视图
@login_required
def export_data(request):
    # 获取当前月份或从查询参数获取
    today = timezone.now()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    status = request.GET.get('status', 'all')
    project_id = request.GET.get('project', None)
    
    # 构建基础查询
    records = ReconciliationRecord.objects.filter(year=year, month=month)
    
    # 根据状态过滤
    if status != 'all' and status in ['waiting', 'exception', 'completed']:
        records = records.filter(status=status)
    
    # 根据项目筛选
    if project_id:
        records = records.filter(project_id=project_id)
    
    # 创建CSV响应
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reconciliation_data_{year}_{month}.csv"'
    
    # 创建CSV写入器
    writer = csv.writer(response)
    writer.writerow([
        '年份', '月份', '项目', '任务', '实际消耗', 'FB消耗', 
        '差异金额', '差异百分比', '状态', '是否手动确认', 
        '确认人', '确认时间', '备注', '创建时间', '更新时间'
    ])
    
    # 写入数据
    for record in records:
        writer.writerow([
            record.year,
            record.month,
            record.project.ProjectName,
            record.task.name,
            record.actual_consumption,
            record.fb_consumption or '',
            record.difference,
            f"{record.difference_percentage}%",
            record.get_status_display(),
            '是' if record.is_manually_confirmed else '否',
            record.confirmed_by.username if record.confirmed_by else '',
            record.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if record.confirmed_at else '',
            record.note,
            record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            record.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

# AJAX视图 - 批量更新FB消耗
@login_required
def batch_update_fb_consumption(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            updates = data.get('updates', [])
            success_count = 0
            
            for update in updates:
                try:
                    record_id = update.get('record_id')
                    fb_consumption = update.get('fb_consumption')
                    note = update.get('note', '')
                    
                    record = ReconciliationRecord.objects.get(id=record_id)
                    
                    # 转换为Decimal类型
                    fb_consumption = Decimal(fb_consumption)
                    old_fb_consumption = record.fb_consumption
                    old_status = record.status
                    
                    record.fb_consumption = fb_consumption
                    if note:
                        record.note = note
                    record.save()
                    
                    # 创建历史记录
                    ReconciliationHistory.objects.create(
                        reconciliation=record,
                        action='update',
                        old_status=old_status,
                        new_status=record.status,
                        old_fb_consumption=old_fb_consumption,
                        new_fb_consumption=record.fb_consumption,
                        difference=record.difference,
                        note=f"批量更新FB消耗: {old_fb_consumption} -> {record.fb_consumption}",
                        operated_by=request.user
                    )
                    
                    success_count += 1
                except (ReconciliationRecord.DoesNotExist, ValueError, decimal.InvalidOperation):
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'成功更新 {success_count} 条记录',
                'updated_count': success_count
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '无效的JSON数据'}, status=400)
    
    return JsonResponse({'success': False, 'message': '仅支持POST请求'}, status=405)

# AJAX视图 - 批量手动确认
@login_required
def batch_manual_confirm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            record_ids = data.get('record_ids', [])
            note = data.get('note', '批量手动确认')
            success_count = 0
            
            for record_id in record_ids:
                try:
                    record = ReconciliationRecord.objects.get(id=record_id)
                    old_status = record.status
                    
                    record.manual_confirm(request.user)
                    
                    # 创建历史记录
                    ReconciliationHistory.objects.create(
                        reconciliation=record,
                        action='confirm',
                        old_status=old_status,
                        new_status='completed',
                        old_fb_consumption=record.fb_consumption,
                        new_fb_consumption=record.fb_consumption,
                        difference=record.difference,
                        note=f"批量手动确认完成对账: {note}",
                        operated_by=request.user
                    )
                    
                    success_count += 1
                except ReconciliationRecord.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'成功确认 {success_count} 条记录',
                'confirmed_count': success_count
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '无效的JSON数据'}, status=400)
    
    return JsonResponse({'success': False, 'message': '仅支持POST请求'}, status=405)

# AJAX API - 获取历史记录
@login_required
def record_history_api(request, record_id):
    """API端点：获取对账记录的历史记录"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': '非法请求'}, status=400)
    
    try:
        record = ReconciliationRecord.objects.get(id=record_id)
    except ReconciliationRecord.DoesNotExist:
        return JsonResponse({'error': '记录不存在'}, status=404)
    
    histories = record.histories.all().order_by('-operated_at')
    
    # 构建历史记录数据
    history_data = []
    for history in histories:
        history_data.append({
            'id': str(history.id),
            'action': history.action,
            'action_display': history.get_action_display(),
            'old_status': history.old_status,
            'old_status_display': dict(ReconciliationRecord.STATUS_CHOICES).get(history.old_status, '') if history.old_status else '',
            'new_status': history.new_status,
            'new_status_display': dict(ReconciliationRecord.STATUS_CHOICES).get(history.new_status, ''),
            'old_fb_consumption': float(history.old_fb_consumption) if history.old_fb_consumption is not None else None,
            'new_fb_consumption': float(history.new_fb_consumption) if history.new_fb_consumption is not None else None,
            'difference': float(history.difference) if history.difference is not None else None,
            'note': history.note,
            'operated_by': history.operated_by.username if history.operated_by else '系统',
            'operated_at': history.operated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({
        'success': True,
        'record_id': str(record.id),
        'histories': history_data
    })

# 获取对账附件API
@login_required
def record_attachments_api(request, record_id):
    """获取对账记录的附件列表"""
    record = get_object_or_404(ReconciliationRecord, id=record_id)
    
    # 获取附件列表
    attachments = record.attachments.order_by('-uploaded_at')
    
    # 构建附件数据
    attachments_data = []
    for attachment in attachments:
        attachments_data.append({
            'id': str(attachment.id),
            'file_name': attachment.file_name,
            'file_size': attachment.file_size,
            'file_url': attachment.file.url,
            'uploaded_by': attachment.uploaded_by.username,
            'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_image': attachment.file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')),
        })
    
    # 返回JSON响应
    return JsonResponse({
        'success': True,
        'record_id': str(record.id),
        'attachments': attachments_data,
        'count': len(attachments_data)
    })
