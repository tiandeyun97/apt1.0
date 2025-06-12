from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Min, Max
from django.utils import timezone
from django.db import transaction
from datetime import date, datetime, timedelta
from calendar import monthrange
from consumption_management.models import TaskConsumption
from task_management.models import Task
from tasks.models import TaskStatus
from .models import ReconciliationRecord, ReconciliationHistory

# 任务状态ID常量
TASK_STATUS_WAITING_RECONCILIATION = 2  # 已结束待对账
TASK_STATUS_COMPLETED_RECONCILIATION = 6  # 已结束完成对账

@receiver(post_save, sender=Task)
def create_reconciliation_for_task(sender, instance, **kwargs):
    """
    当任务状态变为"已结束待对账"时，自动创建对账记录
    1. 查找任务所有的消耗记录
    2. 按月份分组，为每个月创建对账记录
    3. 检查对账记录是否已存在
    """
    # 检查任务状态是否为"已结束待对账"
    if instance.status_id != TASK_STATUS_WAITING_RECONCILIATION:
        return
    
    with transaction.atomic():
        # 获取该任务的所有消耗记录的日期范围
        consumption_data = TaskConsumption.objects.filter(
            task=instance
        ).aggregate(
            min_date=Min('date'),
            max_date=Max('date')
        )
        
        min_date = consumption_data['min_date']
        max_date = consumption_data['max_date']
        
        # 如果没有消耗记录，则不创建对账记录
        if not min_date or not max_date:
            return
        
        # 遍历每个月，创建对账记录
        current_date = date(min_date.year, min_date.month, 1)
        end_date = date(max_date.year, max_date.month, 1)
        
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            
            # 检查是否已存在任何状态的对账记录
            existing_record = ReconciliationRecord.objects.filter(
                year=year,
                month=month,
                task=instance
            ).exists()
            
            # 如果不存在对账记录，则创建新记录
            if not existing_record:
                # 使用ReconciliationRecord的类方法创建对账记录
                # 该方法内部会判断是否有足够的消耗记录来创建对账
                ReconciliationRecord.create_from_task(
                    task=instance,
                    year=year,
                    month=month,
                    user_id=1  # 默认使用ID为1的用户
                )
            
            # 移动到下一个月
            if month == 12:
                current_date = date(year + 1, 1, 1)
            else:
                current_date = date(year, month + 1, 1)

@receiver(post_save, sender=TaskConsumption)
def update_reconciliation_after_consumption_change(sender, instance, **kwargs):
    """
    当TaskConsumption保存时，更新对应的对账记录的实际消耗
    """
    # 获取消耗所属的年月
    consumption_date = instance.date
    year = consumption_date.year
    month = consumption_date.month
    
    # 检查是否存在对应的对账记录
    try:
        reconciliation = ReconciliationRecord.objects.get(
            year=year,
            month=month,
            task=instance.task
        )
    except ReconciliationRecord.DoesNotExist:
        # 如果对账记录不存在，则不需要处理
        return
    
    # 更新对账记录的实际消耗
    with transaction.atomic():
        # 确定日期范围
        start_date = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        
        # 计算该任务在此期间的总实际消耗
        total_consumption = TaskConsumption.objects.filter(
            task=instance.task,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=Sum('actual_consumption'))['total'] or 0
        
        # 更新对账记录
        old_consumption = reconciliation.actual_consumption
        reconciliation.actual_consumption = total_consumption
        reconciliation.save()
        
        # 创建历史记录
        if old_consumption != total_consumption: 
            ReconciliationHistory.objects.create(
                reconciliation=reconciliation,
                action='update',
                old_status=reconciliation.status,
                new_status=reconciliation.status,
                difference=reconciliation.difference,
                note=f'系统自动更新实际消耗: {old_consumption} -> {total_consumption}',
                operated_by_id=1  # 默认使用ID为1的用户
            )

@receiver(post_delete, sender=TaskConsumption)
def recalculate_reconciliation_after_delete(sender, instance, **kwargs):
    """
    当TaskConsumption被删除时，重新计算对应的对账记录
    """
    # 获取消耗所属的年月
    consumption_date = instance.date
    year = consumption_date.year
    month = consumption_date.month
    
    # 查找对应的对账记录
    try:
        reconciliation = ReconciliationRecord.objects.get(
            year=year,
            month=month,
            task=instance.task
        )
    except ReconciliationRecord.DoesNotExist:
        # 如果对账记录不存在，则不需要处理
        return
    
    # 计算该任务在对应月份的总实际消耗
    with transaction.atomic():
        # 确定日期范围
        start_date = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        
        # 计算该任务在此期间的总实际消耗
        total_consumption = TaskConsumption.objects.filter(
            task=instance.task,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=Sum('actual_consumption'))['total'] or 0
        
        # 更新对账记录
        old_consumption = reconciliation.actual_consumption
        reconciliation.actual_consumption = total_consumption
        reconciliation.save()
        
        # 创建历史记录
        if old_consumption != total_consumption:
            ReconciliationHistory.objects.create(
                reconciliation=reconciliation,
                action='update',
                old_status=reconciliation.status,
                new_status=reconciliation.status,
                difference=reconciliation.difference,
                note=f'删除消耗记录后系统自动更新实际消耗: {old_consumption} -> {total_consumption}',
                operated_by_id=1  # 默认使用ID为1的用户
            ) 