from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from .models import Pixel
from task_management.models import Task
from tasks.models import Project
from task_management.permissions import TaskPermission

# Create your views here.

@login_required
def check_task_availability(request):
    """检查任务是否可以被绑定像素的API"""
    task_id = request.GET.get('task_id')
    pixel_id = request.GET.get('pixel_id', '0') 
    
    # 如果没有提供task_id，返回错误
    if not task_id:
        return JsonResponse({'available': False, 'message': '未提供任务ID'})
    
    try:
        # 检查当前任务是否已经被绑定到其他像素
        existing_pixel = Pixel.objects.filter(task_id=task_id).exclude(id=pixel_id).first()
        
        if existing_pixel:
            return JsonResponse({
                'available': False, 
                'pixel_id': existing_pixel.pixel_id,
                'message': f'此任务已被像素ID为 {existing_pixel.pixel_id} 的记录关联！一个任务只能关联一个像素。'
            })
        else:
            return JsonResponse({'available': True})
    except Exception as e:
        return JsonResponse({'available': False, 'message': f'检查失败: {str(e)}'}, status=500)

@login_required
def pixel_list(request):
    """像素列表视图"""
    query_pixel_id = request.GET.get('pixel_id', '')
    query_task = request.GET.get('task', '')
    query_is_authorized = request.GET.get('is_authorized', '')
    query_account = request.GET.get('account', '')
    per_page = request.GET.get('per_page', '20')  # 默认每页20条
    
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 50, 100]:
            per_page = 20
    except ValueError:
        per_page = 20
    
    # 构建查询
    pixels = Pixel.objects.select_related('task', 'creator', 'task__project').all().order_by('-created_at')
    
    # 应用任务权限过滤 - 只显示用户有权限查看的任务相关的像素
    # 获取用户可访问的任务
    user_tasks = TaskPermission.filter_tasks_by_role(Task.objects.all(), request.user)
    pixels = pixels.filter(task__in=user_tasks)
    
    if query_pixel_id:
        pixels = pixels.filter(pixel_id__icontains=query_pixel_id)
    
    if query_task:
        pixels = pixels.filter(task__name__icontains=query_task)
    
    if query_is_authorized:
        is_authorized_value = True if query_is_authorized == 'True' else False
        pixels = pixels.filter(is_authorized=is_authorized_value)
        
    if query_account:
        pixels = pixels.filter(account__icontains=query_account)
    
    # 分页处理
    paginator = Paginator(pixels, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'admin/pixel_management/pixel/pixel_list.html', context)

@login_required
def pixel_detail(request, pk):
    """像素详情视图"""
    # 获取像素对象
    pixel = get_object_or_404(
        Pixel.objects.select_related('task', 'creator', 'task__project'), 
        pk=pk
    )
    
    # 检查用户是否有权限查看此像素对应的任务
    user_tasks = TaskPermission.filter_tasks_by_role(Task.objects.filter(id=pixel.task.id), request.user)
    if not user_tasks.exists():
        messages.error(request, '您没有权限查看此像素')
        return redirect('pixel_management:pixel_list')
    
    # 如果是AJAX请求，返回详情卡片模板
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            'admin/pixel_management/pixel/pixel_detail_card.html',
            {'pixel': pixel},
            request=request
        )
        return HttpResponse(html)
    
    return render(request, 'admin/pixel_management/pixel/pixel_detail.html', {'pixel': pixel})

@login_required
@permission_required('pixel_management.add_pixel', raise_exception=True)
def pixel_create(request):
    """创建像素视图"""
    if request.method == 'POST':
        # 处理表单提交
        task_id = request.POST.get('task')
        task = get_object_or_404(Task, id=task_id)
        
        # 检查用户是否有权限操作此任务
        user_tasks = TaskPermission.filter_tasks_by_role(Task.objects.filter(id=task_id), request.user)
        if not user_tasks.exists():
            messages.error(request, '您没有权限为此任务创建像素')
            return redirect('pixel_management:pixel_list')
        
        # 检查任务是否已经绑定了像素
        if Pixel.objects.filter(task=task).exists():
            existing_pixel = Pixel.objects.get(task=task)
            messages.error(request, f'此任务已被像素ID为 {existing_pixel.pixel_id} 的记录关联！一个任务只能关联一个像素。')
            return redirect('pixel_management:pixel_create')
        
        # 获取表单数据
        pixel_id = request.POST.get('pixel_id')
        bm_id = request.POST.get('bm_id')
        
        # 创建像素记录
        pixel = Pixel(
            pixel_id=pixel_id,
            task=task,
            bm_id=bm_id,
            account=request.POST.get('account'),
            timezone=request.POST.get('timezone'),
            is_authorized=request.POST.get('is_authorized') == 'True',
            notes=request.POST.get('notes'),
            creator=request.user  # 自动设置创建人
        )
        
        pixel.save()
        messages.success(request, '像素创建成功！')
        return redirect('pixel_management:pixel_list')
    
    # GET请求显示表单
    # 只获取当前用户可访问的任务
    tasks = TaskPermission.filter_tasks_by_role(
        Task.objects.all(), request.user
    ).select_related('project').order_by('-created_at')
    
    context = {
        'title': '新建像素',
        'tasks': tasks,
    }
    
    # 如果是AJAX请求，返回表单页面
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'admin/pixel_management/pixel/pixel_form.html', context)
        
    return render(request, 'admin/pixel_management/pixel/pixel_form.html', context)

@login_required
@permission_required('pixel_management.change_pixel', raise_exception=True)
def pixel_edit(request, pk):
    """编辑像素视图"""
    pixel = get_object_or_404(Pixel, pk=pk)
    
    # 检查用户是否有权限操作此像素对应的任务
    user_tasks = TaskPermission.filter_tasks_by_role(Task.objects.filter(id=pixel.task.id), request.user)
    if not user_tasks.exists():
        messages.error(request, '您没有权限编辑此像素')
        return redirect('pixel_management:pixel_list')
    
    if request.method == 'POST':
        # 处理表单提交
        task_id = request.POST.get('task')
        task = get_object_or_404(Task, id=task_id)
        
        # 检查用户是否有权限操作新选择的任务
        user_tasks = TaskPermission.filter_tasks_by_role(Task.objects.filter(id=task_id), request.user)
        if not user_tasks.exists():
            messages.error(request, '您没有权限将像素关联到此任务')
            return redirect('pixel_management:pixel_edit', pk=pk)
        
        # 检查任务是否已经绑定了其他像素
        existing_pixel = Pixel.objects.filter(task=task).exclude(id=pk).first()
        if existing_pixel:
            messages.error(request, f'此任务已被像素ID为 {existing_pixel.pixel_id} 的记录关联！一个任务只能关联一个像素。')
            return redirect('pixel_management:pixel_edit', pk=pk)
            
        # 更新像素记录
        pixel.pixel_id = request.POST.get('pixel_id')
        pixel.task = task
        pixel.bm_id = request.POST.get('bm_id')
        pixel.account = request.POST.get('account')
        pixel.timezone = request.POST.get('timezone')
        pixel.is_authorized = request.POST.get('is_authorized') == 'True'
        pixel.notes = request.POST.get('notes')
        
        pixel.save()
        messages.success(request, '像素更新成功！')
        return redirect('pixel_management:pixel_list')
    
    # GET请求显示表单
    tasks = TaskPermission.filter_tasks_by_role(
        Task.objects.all(), request.user
    ).select_related('project').order_by('-created_at')
    
    context = {
        'pixel': pixel,
        'title': '编辑像素',
        'tasks': tasks,
    }
    return render(request, 'admin/pixel_management/pixel/pixel_form.html', context)

@login_required
@permission_required('pixel_management.change_pixel', raise_exception=True)
def toggle_authorization(request, pk):
    """切换像素授权状态的API"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '请求方法不允许'}, status=405)
    
    try:
        pixel = get_object_or_404(Pixel, pk=pk)
        
        # 检查用户是否有权限操作此像素对应的任务
        user_tasks = TaskPermission.filter_tasks_by_role(Task.objects.filter(id=pixel.task.id), request.user)
        if not user_tasks.exists():
            return JsonResponse({'status': 'error', 'message': '您没有权限修改此像素的授权状态'}, status=403)
        
        # 切换授权状态
        pixel.is_authorized = not pixel.is_authorized
        pixel.save(update_fields=['is_authorized', 'updated_at'])
        
        return JsonResponse({
            'status': 'success',
            'is_authorized': pixel.is_authorized,
            'display_status': '已授权' if pixel.is_authorized else '未授权',
            'message': '已' + ('授权' if pixel.is_authorized else '取消授权')
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'操作失败: {str(e)}'}, status=500)

@login_required
@permission_required('pixel_management.delete_pixel', raise_exception=True)
def pixel_delete(request, pk):
    """删除像素视图"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '请求方法不允许'}, status=405)
    
    try:
        pixel = get_object_or_404(Pixel, pk=pk)
        
        # 检查用户是否有权限操作此像素对应的任务
        user_tasks = TaskPermission.filter_tasks_by_role(Task.objects.filter(id=pixel.task.id), request.user)
        if not user_tasks.exists():
            return JsonResponse({'status': 'error', 'message': '您没有权限删除此像素'}, status=403)
        
        pixel.delete()
        return JsonResponse({
            'status': 'success',
            'message': '像素已成功删除'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'删除失败: {str(e)}'}, status=500)
