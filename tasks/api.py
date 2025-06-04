from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from organize.models import User
from .models import Project
import logging

logger = logging.getLogger(__name__)

@login_required
@permission_required('tasks.view_project')
def project_detail_api(request, project_id):
    """获取项目详情的API视图"""
    try:
        logger.info(f"Fetching project info for project_id: {project_id}")
        project = get_object_or_404(Project, ProjectID=project_id)
        
        # 检查用户权限
        if not request.user.is_superuser and project.CompanyID != request.user.company:
            return JsonResponse({
                'success': False,
                'message': '无权访问此项目信息',
                'code': 403
            })
            
        # 构建响应数据
        data = {
            'success': True,
            'data': {
                'ProjectName': project.ProjectName,
                'MediaChannelName': project.MediaChannelID.MediaChannelName if project.MediaChannelID else '',
                'TaskTypeName': project.TaskTypeID.TaskTypeName if project.TaskTypeID else '',
                'TimeZone': project.TimeZone or '',
                'KPI': project.KPI or '',
                'DailyReportURL': project.DailyReportURL or '',
                'ManagerID': project.ManagerID.id if project.ManagerID else None,
                'ManagerName': project.ManagerID.get_full_name() or project.ManagerID.username if project.ManagerID else '',
                'StartDate': project.StartDate.strftime('%Y-%m-%d') if project.StartDate else '',
                'EndDate': project.EndDate.strftime('%Y-%m-%d') if project.EndDate else '',
                'Description': project.Description or ''
            }
        }
        logger.info(f"Successfully fetched project info for project_id: {project_id}")
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error fetching project info: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'获取项目信息失败: {str(e)}',
            'code': 500
        })

@login_required
@permission_required('tasks.view_project')
def get_optimizers(request):
    """获取优化师列表的API视图"""
    try:
        # 获取当前用户所在公司的优化师
        optimizers = User.objects.filter(
            company=request.user.company,
            groups__name__in=['优化师', '部门主管'],
            is_active=True
        ).distinct()
        
        # 构建响应数据
        data = {
            'success': True,
            'data': [
                {
                    'id': optimizer.id,
                    'name': optimizer.get_full_name() or optimizer.username
                }
                for optimizer in optimizers
            ]
        }
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error fetching optimizers: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'获取优化师列表失败: {str(e)}',
            'code': 500
        }) 