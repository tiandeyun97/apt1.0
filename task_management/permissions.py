from django.db.models import Q
from .models import Task
from organize.models import Department, User

class TaskPermission:
    """
    任务权限控制类，用于根据用户角色过滤任务数据
    
    权限规则：
    1. 优化师：只能看到自己的任务
    2. 小组长：可以看到自己和组内所有成员的任务
    3. 部门主管：可以看到本部门和所有子部门的任务
    4. 其他角色：可以看到公司内的所有任务
    """
    
    @staticmethod
    def filter_tasks_by_role(queryset, user):
        """
        根据用户角色过滤任务数据
        
        Args:
            queryset: 任务查询集
            user: 当前用户对象
            
        Returns:
            过滤后的任务查询集
        """
        if not user.is_authenticated:
            return queryset.none()  # 用户未登录，返回空查询集
        
        # 确保只能看到自己公司的数据
        queryset = queryset.filter(company=user.company)
        
        # 获取用户所属的组（角色）
        user_groups = [group.name for group in user.groups.all()]
        
        # 1. 如果用户是优化师角色
        if '优化师' in user_groups and not any(role in user_groups for role in ['部门主管', '小组长']):
            filtered = queryset.filter(optimizer=user).distinct()
            return filtered
        
        # 2. 如果用户是小组长角色
        elif '小组长' in user_groups and '部门主管' not in user_groups:
            # 获取小组长所在的部门
            try:
                departments = user.department.all()
                
                if not departments:
                    return queryset.filter(optimizer=user).distinct()  # 如果没有部门，只显示自己的任务
                
                # 获取部门的所有成员ID
                team_member_ids = []
                for dept in departments:
                    members = dept.members.all()
                    member_ids = [member.id for member in members]
                    team_member_ids.extend(member_ids)
                
                # 添加小组长自己的ID
                team_member_ids.append(user.id)
                team_member_ids = list(set(team_member_ids))  # 去重
                
                # 过滤任务：优化师是部门成员的任务，使用distinct()防止重复
                filtered = queryset.filter(optimizer__id__in=team_member_ids).distinct()
                return filtered
            except Exception as e:
                # 如果出现异常，只返回自己的任务
                return queryset.filter(optimizer=user).distinct()
        
        # 3. 如果用户是部门主管角色
        elif '部门主管' in user_groups:
            try:
                # 获取部门主管管理的部门
                managed_department = user.managed_department
                
                if not managed_department:
                    return queryset.filter(optimizer=user).distinct()  # 如果没有管理部门，只显示自己的任务
                
                # 获取当前部门及所有子部门
                dept_ids = [managed_department.department_id]
                
                # 递归获取所有子部门ID
                def get_child_dept_ids(parent_id):
                    children = Department.objects.filter(parent_department_id=parent_id)
                    for child in children:
                        dept_ids.append(child.department_id)
                        get_child_dept_ids(child.department_id)
                
                get_child_dept_ids(managed_department.department_id)
                
                # 获取这些部门的所有成员ID
                member_ids = []
                for dept_id in dept_ids:
                    dept = Department.objects.get(department_id=dept_id)
                    dept_members = [member.id for member in dept.members.all()]
                    member_ids.extend(dept_members)
                    # 如果有部门负责人，也加入成员列表
                    if dept.manager:
                        member_ids.append(dept.manager.id)
                
                # 添加部门主管自己的ID
                member_ids.append(user.id)
                member_ids = list(set(member_ids))  # 去重
                
                # 过滤任务：优化师是部门成员的任务，使用distinct()防止重复
                filtered = queryset.filter(optimizer__id__in=member_ids).distinct()
                return filtered
            except Exception as e:
                # 如果出现异常，只返回自己的任务
                return queryset.filter(optimizer=user).distinct()
        
        # 4. 其他角色（如管理员）显示公司内所有任务
        return queryset.distinct()


def get_filtered_tasks(user):
    """
    获取当前用户可以查看的任务列表的便捷方法
    
    Args:
        user: 当前用户对象
        
    Returns:
        过滤后的任务查询集
    """
    queryset = Task.objects.all()
    return TaskPermission.filter_tasks_by_role(queryset, user) 