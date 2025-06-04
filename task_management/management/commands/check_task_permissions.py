from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from organize.models import User, Department
from task_management.models import Task
from task_management.permissions import TaskPermission

class Command(BaseCommand):
    help = '检查用户任务权限和关联关系'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='要检查的用户名（可选）')

    def handle(self, *args, **options):
        username = options.get('username')
        
        if username:
            # 检查特定用户
            try:
                user = User.objects.get(username=username)
                self.check_user(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'用户 {username} 不存在'))
        else:
            # 检查所有用户
            for user in User.objects.all():
                self.check_user(user)
    
    def check_user(self, user):
        self.stdout.write(self.style.NOTICE(f'检查用户: {user.username} (ID: {user.id})'))
        
        # 检查用户角色
        groups = [group.name for group in user.groups.all()]
        self.stdout.write(f'  角色: {", ".join(groups) if groups else "无"}')
        
        # 检查用户部门
        departments = user.department.all()
        self.stdout.write(f'  所属部门: {", ".join([dept.name for dept in departments]) if departments.exists() else "无"}')
        
        # 检查管理的部门
        try:
            managed_dept = user.managed_department
            self.stdout.write(f'  管理的部门: {managed_dept.name if managed_dept else "无"}')
        except:
            self.stdout.write(f'  管理的部门: 无')
        
        # 检查关联的任务
        optimized_tasks = user.optimized_tasks.all()
        self.stdout.write(f'  关联的任务数: {optimized_tasks.count()}')
        
        if optimized_tasks:
            self.stdout.write('  关联的任务:')
            for task in optimized_tasks[:5]:  # 只显示前5个任务
                self.stdout.write(f'    - ID: {task.id}, 名称: {task.name}')
            if optimized_tasks.count() > 5:
                self.stdout.write(f'    ... 还有 {optimized_tasks.count() - 5} 个任务')
        
        # 检查可访问的任务
        all_tasks = Task.objects.all()
        visible_tasks = TaskPermission.filter_tasks_by_role(all_tasks, user)
        self.stdout.write(f'  可访问的任务数: {visible_tasks.count()} (总任务数: {all_tasks.count()})')
        
        if visible_tasks.count() != optimized_tasks.count():
            self.stdout.write(self.style.WARNING(f'  警告: 可访问的任务数与关联的任务数不一致!'))
            # 检查是否有任务显示给了不该看到的用户
            if visible_tasks.count() > optimized_tasks.count():
                extra_tasks = visible_tasks.exclude(id__in=[task.id for task in optimized_tasks])
                self.stdout.write(self.style.ERROR(f'  错误: 用户可以看到 {extra_tasks.count()} 个不应该看到的任务!'))
                for task in extra_tasks[:3]:
                    self.stdout.write(self.style.ERROR(f'    - ID: {task.id}, 名称: {task.name}'))
                
                # 检查这些任务的优化师是谁
                for task in extra_tasks[:3]:
                    task_optimizers = task.optimizer.all()
                    self.stdout.write(self.style.ERROR(f'    任务 {task.name} 的优化师: {", ".join([opt.username for opt in task_optimizers])}'))
        
        self.stdout.write('')  # 空行分隔不同用户 