from organize.models import Department, User
from django.db.models import Q
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)

def check_task_consumption_permission(user, task, action="view"):
    """
    检查用户是否有权限对任务消耗数据进行操作
    
    参数:
        user: 当前用户
        task: 任务对象
        action: 操作类型，可选值为 "view", "add", "edit", "delete"
        
    返回:
        bool: 是否有权限
    """
    # 记录当前用户和任务信息
    logger.info(f"权限检查: 用户={user.username}, 任务ID={task.id}, 操作={action}")
    
    # 如果是超级管理员，可以进行所有操作
    if user.is_superuser:
        logger.info(f"超级管理员权限检查: 通过")
        return True
        
    # 非超级管理员只能操作本公司的数据
    if task.company != user.company:
        logger.info(f"权限检查: 公司不匹配 - 拒绝访问")
        return False
    
    # 根据用户角色进行权限控制
    if user.groups.filter(name__in=['管理员', '运营']).exists():
        # 管理员和运营可以对本公司的数据进行所有操作
        logger.info(f"管理员/运营权限检查: 通过")
        return True
    
    elif user.groups.filter(name='部门主管').exists():
        logger.info(f"部门主管权限检查")
        # 如果是部门主管，需要查看这个部门管理的用户是否包含任务的优化师
        try:
            # 1. 自己是优化师或创建者
            task_optimizers = list(task.optimizer.all().values_list('id', flat=True))
            
            if user in task.optimizer.all() or task.creator == user:
                logger.info(f"部门主管权限检查: 是任务优化师或创建者 - 通过")
                return True
                
            # 2. 尝试获取用户管理的部门
            departments = Department.objects.filter(manager=user)
            if not departments.exists():
                logger.warning(f"部门主管权限检查: 未找到管理的部门 - 拒绝访问")
                return False
                
            department = departments.first()
            logger.info(f"部门主管权限检查: 管理部门={department.department_name}")
            
            # 3. 获取该部门的所有用户
            dept_members = list(department.members.all().values_list('id', flat=True))
            logger.info(f"部门成员ID: {dept_members}")
            logger.info(f"任务优化师ID: {task_optimizers}")
            
            # 检查任务优化师是否在部门成员中
            for optimizer_id in task_optimizers:
                if optimizer_id in dept_members:
                    logger.info(f"部门主管权限检查: 任务优化师在部门成员中 - 通过")
                    return True
            
            # 4. 获取子部门的所有用户
            child_departments = Department.objects.filter(parent_department=department)
            logger.info(f"子部门数量: {child_departments.count()}")
            
            for child_dept in child_departments:
                child_members = list(child_dept.members.all().values_list('id', flat=True))
                logger.info(f"子部门 {child_dept.department_name} 成员ID: {child_members}")
                
                for optimizer_id in task_optimizers:
                    if optimizer_id in child_members:
                        logger.info(f"部门主管权限检查: 任务优化师在子部门成员中 - 通过")
                        return True
            
            # 5. 获取孙部门的所有用户
            for child_dept in child_departments:
                grandchild_departments = Department.objects.filter(parent_department=child_dept)
                logger.info(f"孙部门数量: {grandchild_departments.count()}")
                
                for grandchild_dept in grandchild_departments:
                    grandchild_members = list(grandchild_dept.members.all().values_list('id', flat=True))
                    logger.info(f"孙部门 {grandchild_dept.department_name} 成员ID: {grandchild_members}")
                    
                    for optimizer_id in task_optimizers:
                        if optimizer_id in grandchild_members:
                            logger.info(f"部门主管权限检查: 任务优化师在孙部门成员中 - 通过")
                            return True
            
            logger.warning(f"部门主管权限检查: 未找到匹配的部门成员 - 拒绝访问")
            return False
            
        except Exception as e:
            logger.error(f"部门主管权限检查错误：{str(e)}")
            return False
            
    elif user.groups.filter(name='小组长').exists():
        logger.info(f"小组长权限检查")
        # 如果是小组长，需要查看这个二级部门的所有优化师是否包含任务的优化师
        try:
            # 1. 自己是优化师或创建者
            if user in task.optimizer.all() or task.creator == user:
                logger.info(f"小组长权限检查: 是任务优化师或创建者 - 通过")
                return True
                
            # 2. 获取用户所在的二级部门
            departments = Department.objects.filter(manager=user)
            if not departments.exists():
                logger.warning(f"小组长权限检查: 未找到管理的部门 - 拒绝访问")
                return False
                
            # 3. 获取这些二级部门的所有用户
            task_optimizers = list(task.optimizer.all().values_list('id', flat=True))
            
            for dept in departments:
                dept_members = list(dept.members.all().values_list('id', flat=True))
                logger.info(f"部门 {dept.department_name} 成员ID: {dept_members}")
                logger.info(f"任务优化师ID: {task_optimizers}")
                
                for optimizer_id in task_optimizers:
                    if optimizer_id in dept_members:
                        logger.info(f"小组长权限检查: 任务优化师在部门成员中 - 通过")
                        return True
                    
            logger.warning(f"小组长权限检查: 未找到匹配的部门成员 - 拒绝访问")
            return False
        except Exception as e:
            logger.error(f"小组长权限检查错误：{e}")
            return False
            
    elif user.groups.filter(name='优化师').exists():
        # 优化师只能查看/编辑自己的任务数据
        result = user in task.optimizer.all() or task.creator == user
        logger.info(f"优化师权限检查: {'通过' if result else '拒绝访问'}")
        return result
        
    else:
        # 其他角色只能查看自己创建的记录
        result = task.creator == user
        logger.info(f"其他角色权限检查: {'通过' if result else '拒绝访问'}")
        return result

def get_all_department_users(department):
    """获取部门及其所有下级部门的用户"""
    # 记录日志
    logger.info(f"获取部门用户: 部门={department.department_name}")
    
    # 获取本部门成员
    all_users_ids = list(department.members.all().values_list('id', flat=True))
    logger.info(f"本部门成员ID: {all_users_ids}")
    
    # 获取直接子部门
    child_departments = Department.objects.filter(parent_department=department)
    logger.info(f"子部门数量: {child_departments.count()}")
    
    for child_dept in child_departments:
        # 获取子部门用户
        child_member_ids = list(child_dept.members.all().values_list('id', flat=True))
        logger.info(f"子部门 {child_dept.department_name} 成员ID: {child_member_ids}")
        all_users_ids.extend(child_member_ids)
        
        # 获取孙部门
        grandchild_departments = Department.objects.filter(parent_department=child_dept)
        logger.info(f"孙部门数量: {grandchild_departments.count()}")
        
        for grandchild_dept in grandchild_departments:
            grandchild_member_ids = list(grandchild_dept.members.all().values_list('id', flat=True))
            logger.info(f"孙部门 {grandchild_dept.department_name} 成员ID: {grandchild_member_ids}")
            all_users_ids.extend(grandchild_member_ids)
    
    # 去重
    unique_ids = list(set(all_users_ids))
    logger.info(f"最终所有用户ID: {unique_ids}")
    return unique_ids

def filter_queryset_by_role(queryset, user, model_type="taskconsumption"):
    """
    根据用户角色过滤查询集
    
    参数:
        queryset: 原始查询集
        user: 当前用户
        model_type: 模型类型，可选值为 "taskconsumption", "task"
        
    返回:
        filtered_queryset: 过滤后的查询集
    """
    # 记录当前用户
    logger.info(f"过滤查询集: 用户={user.username}, 模型类型={model_type}")
    
    # 如果是超级管理员，可以查看所有数据
    if user.is_superuser:
        logger.info(f"超级管理员过滤: 显示所有数据")
        return queryset
        
    # 非超级管理员只能查看本公司数据
    if model_type == "taskconsumption":
        queryset = queryset.filter(task__company=user.company)
    else:
        queryset = queryset.filter(company=user.company)
    
    # 根据用户角色进行过滤
    if user.groups.filter(name__in=['管理员', '运营']).exists():
        # 管理员和运营可以查看全部数据(公司范围内)
        logger.info(f"管理员/运营过滤: 显示公司所有数据")
        return queryset
        
    elif user.groups.filter(name='部门主管').exists():
        logger.info(f"部门主管过滤")
        try:
            # 1. 获取部门主管管理的部门
            departments = Department.objects.filter(manager=user)
            if not departments.exists():
                logger.warning(f"部门主管过滤: 未找到管理的部门 - 只显示个人数据")
                if model_type == "taskconsumption":
                    return queryset.filter(Q(creator=user) | Q(task__optimizer=user)).distinct()
                else:
                    # Task模型没有creator字段，只用optimizer过滤
                    return queryset.filter(optimizer=user).distinct()
            
            department = departments.first()
            logger.info(f"部门主管过滤: 管理部门={department.department_name}")
            
            # 2. 获取该部门及所有下级部门的用户ID
            dept_user_ids = get_all_department_users(department)
            
            # 3. 添加自己的ID
            if user.id not in dept_user_ids:
                dept_user_ids.append(user.id)
                
            logger.info(f"部门主管过滤: 所有部门成员ID={dept_user_ids}")
            
            # 4. 构建过滤条件
            if model_type == "taskconsumption":
                result = queryset.filter(
                    Q(task__optimizer__id__in=dept_user_ids) |  # 任务优化师是部门成员
                    Q(creator_id__in=dept_user_ids)              # 创建者是部门成员
                ).distinct()
                logger.info(f"部门主管过滤: 查询到 {result.count()} 条记录")
                return result
            else:
                # Task模型没有creator字段，只用optimizer过滤
                result = queryset.filter(
                    optimizer__id__in=dept_user_ids  # 优化师是部门成员
                ).distinct()
                logger.info(f"部门主管过滤: 查询到 {result.count()} 条记录")
                return result
                
        except Exception as e:
            logger.error(f"部门主管数据过滤错误：{str(e)}")
            # 如果出错，至少能看到自己的数据
            if model_type == "taskconsumption":
                return queryset.filter(Q(creator=user) | Q(task__optimizer=user)).distinct()
            else:
                # Task模型没有creator字段，只用optimizer过滤
                return queryset.filter(optimizer=user).distinct()
    
    elif user.groups.filter(name='小组长').exists():
        logger.info(f"小组长过滤")
        try:
            # 1. 获取小组长领导的部门
            departments = Department.objects.filter(manager=user)
            if not departments.exists():
                logger.warning(f"小组长过滤: 未找到管理的部门 - 只显示个人数据")
                if model_type == "taskconsumption":
                    return queryset.filter(Q(creator=user) | Q(task__optimizer=user)).distinct()
                else:
                    # Task模型没有creator字段，只用optimizer过滤
                    return queryset.filter(optimizer=user).distinct()
            
            # 2. 获取这些部门的所有用户ID
            dept_user_ids = [user.id]  # 包括自己
            for dept in departments:
                dept_member_ids = list(dept.members.all().values_list('id', flat=True))
                logger.info(f"部门 {dept.department_name} 成员ID: {dept_member_ids}")
                dept_user_ids.extend(dept_member_ids)
            
            # 去重
            dept_user_ids = list(set(dept_user_ids))
            logger.info(f"小组长过滤: 所有部门成员ID={dept_user_ids}")
            
            # 3. 构建过滤条件
            if model_type == "taskconsumption":
                result = queryset.filter(
                    Q(task__optimizer__id__in=dept_user_ids) |  # 任务优化师是部门成员
                    Q(creator_id__in=dept_user_ids)              # 创建者是部门成员
                ).distinct()
                logger.info(f"小组长过滤: 查询到 {result.count()} 条记录")
                return result
            else:
                # Task模型没有creator字段，只用optimizer过滤
                result = queryset.filter(
                    optimizer__id__in=dept_user_ids  # 优化师是部门成员
                ).distinct()
                logger.info(f"小组长过滤: 查询到 {result.count()} 条记录")
                return result
                
        except Exception as e:
            logger.error(f"小组长数据过滤错误：{str(e)}")
            # 如果出错，至少能看到自己的数据
            if model_type == "taskconsumption":
                return queryset.filter(Q(creator=user) | Q(task__optimizer=user)).distinct()
            else:
                # Task模型没有creator字段，只用optimizer过滤
                return queryset.filter(optimizer=user).distinct()
    
    elif user.groups.filter(name='优化师').exists():
        # 优化师只能查看自己的任务数据
        logger.info(f"优化师过滤: 只显示个人数据")
        if model_type == "taskconsumption":
            result = queryset.filter(Q(creator=user) | Q(task__optimizer=user)).distinct()
            logger.info(f"优化师过滤: 查询到 {result.count()} 条记录")
            return result
        else:
            # Task模型没有creator字段，只用optimizer过滤
            result = queryset.filter(optimizer=user).distinct()
            logger.info(f"优化师过滤: 查询到 {result.count()} 条记录")
            return result
    else:
        # 其他角色只能看自己创建的数据
        logger.info(f"其他角色过滤: 只显示创建的数据")
        if model_type == "taskconsumption":
            result = queryset.filter(creator=user)
            logger.info(f"其他角色过滤: 查询到 {result.count()} 条记录")
            return result
        else:
            # Task模型没有creator字段，只用optimizer过滤
            result = queryset.filter(optimizer=user)
            logger.info(f"其他角色过滤: 查询到 {result.count()} 条记录")
            return result 