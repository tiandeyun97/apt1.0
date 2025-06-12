from django.db import models
from django.utils import timezone
import uuid
from task_management.models import Task
from tasks.models import Project
from consumption_management.models import TaskConsumption
from organize.models import User
from datetime import datetime
from django.db.models import Sum
from decimal import Decimal

class ReconciliationRecord(models.Model):
    """对账记录模型"""
    STATUS_CHOICES = [
        ('waiting', '等待对账'),
        ('completed', '完成对账'),
        ('exception', '异常对账'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.IntegerField('年份')
    month = models.IntegerField('月份')
    project = models.ForeignKey(Project, verbose_name='所属项目', on_delete=models.PROTECT, related_name='reconciliation_records')
    task = models.ForeignKey(Task, verbose_name='关联任务', on_delete=models.CASCADE, related_name='reconciliation_records')
    actual_consumption = models.DecimalField('实际消耗总额', max_digits=12, decimal_places=2, default=0)
    fb_consumption = models.DecimalField('FB消耗', max_digits=12, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField('差异金额', max_digits=12, decimal_places=2, default=0)
    difference_percentage = models.DecimalField('差异百分比', max_digits=6, decimal_places=2, default=0)
    status = models.CharField('对账状态', max_length=20, choices=STATUS_CHOICES, default='waiting')
    is_manually_confirmed = models.BooleanField('是否手动确认', default=False)
    confirmed_by = models.ForeignKey(User, verbose_name='确认人', on_delete=models.PROTECT, related_name='confirmed_records', null=True, blank=True)
    confirmed_at = models.DateTimeField('确认时间', null=True, blank=True)
    note = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '对账记录'
        verbose_name_plural = '对账记录'
        ordering = ['-year', '-month', 'project__ProjectName', 'task__name']
        unique_together = ('year', 'month', 'task')
    
    def __str__(self):
        return f"{self.year}年{self.month}月 - {self.project.ProjectName} - {self.task.name}"
    
    def get_difference(self):
        """获取差异金额"""
        if self.fb_consumption is None:
            return 0
        return self.difference
    
    def get_difference_percentage(self):
        """获取差异百分比"""
        if self.fb_consumption is None:
            return 0
        return self.difference_percentage
    
    def get_absolute_difference(self):
        """获取差异金额的绝对值"""
        if self.fb_consumption is None:
            return 0
        return abs(self.difference)
    
    def get_absolute_difference_percentage(self):
        """获取差异百分比的绝对值"""
        if self.fb_consumption is None:
            return 0
        return abs(self.difference_percentage)
    
    def save(self, *args, **kwargs):
        # 计算差异金额
        if self.fb_consumption is not None:
            # 确保类型一致，强制转换为Decimal类型
            if not isinstance(self.fb_consumption, Decimal):
                self.fb_consumption = Decimal(str(self.fb_consumption))
            if not isinstance(self.actual_consumption, Decimal):
                self.actual_consumption = Decimal(str(self.actual_consumption))
            
            self.difference = self.fb_consumption - self.actual_consumption
            
            # 计算差异百分比
            if self.actual_consumption:
                self.difference_percentage = (self.difference / self.actual_consumption) * 100
            else:
                # 当实际消耗为0但FB消耗不为0时，设置一个非常大的差异百分比，确保标记为异常
                if self.fb_consumption > 0:
                    self.difference_percentage = 100  # 设置为100%差异
                else:
                    self.difference_percentage = 0
            
            # 自动判断对账状态
            tolerance = 5  # 设置容错范围为5%
            
            # 修改判断逻辑：如果是手动确认的，直接设为完成状态，否则根据差异判断
            if self.is_manually_confirmed:
                self.status = 'completed'
            elif self.actual_consumption == 0 and self.fb_consumption > 0:
                # 实际消耗为0但有FB消耗，直接标记为异常
                self.status = 'exception'
            elif abs(self.difference_percentage) <= tolerance:
                self.status = 'completed'
            else:
                self.status = 'exception'
        else:
            self.status = 'waiting'
            
        super().save(*args, **kwargs)
    
    def manual_confirm(self, user):
        """手动确认完成对账"""
        self.is_manually_confirmed = True
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.status = 'completed'
        self.save()
    
    @classmethod
    def create_from_task(cls, task, year, month, user_id=1):
        """
        从任务创建对账记录
        """
        import datetime as dt
        from calendar import monthrange
        
        # 确定日期范围
        start_date = dt.date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = dt.date(year, month, last_day)
        
        # 计算任务在指定周期内的总实际消耗
        total_consumption = TaskConsumption.objects.filter(
            task=task,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=Sum('actual_consumption'))['total'] or 0
        
        # 如果整月消耗为0，则跳过创建对账记录
        if total_consumption == 0:
            return None
        
        # 创建对账记录
        record = cls.objects.create(
            year=year,
            month=month,
            project=task.project,
            task=task,
            actual_consumption=total_consumption,
            status='waiting'  # 默认为"等待对账"状态
        )
        
        # 创建历史记录
        ReconciliationHistory.objects.create(
            reconciliation=record,
            action='create',
            new_status='waiting',
            note='系统根据任务状态变更自动创建对账记录',
            operated_by_id=user_id
        )
        
        return record

class ReconciliationHistory(models.Model):
    """对账历史记录模型"""
    ACTION_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('confirm', '手动确认'),
        ('system_confirm', '系统确认'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reconciliation = models.ForeignKey(ReconciliationRecord, verbose_name='对账记录', on_delete=models.CASCADE, related_name='histories')
    action = models.CharField('操作类型', max_length=20, choices=ACTION_CHOICES)
    old_status = models.CharField('旧状态', max_length=20, choices=ReconciliationRecord.STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField('新状态', max_length=20, choices=ReconciliationRecord.STATUS_CHOICES)
    old_fb_consumption = models.DecimalField('旧FB消耗', max_digits=12, decimal_places=2, null=True, blank=True)
    new_fb_consumption = models.DecimalField('新FB消耗', max_digits=12, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField('差异金额', max_digits=12, decimal_places=2, null=True, blank=True)
    note = models.TextField('备注', blank=True)
    operated_by = models.ForeignKey(User, verbose_name='操作人', on_delete=models.PROTECT, related_name='reconciliation_histories')
    operated_at = models.DateTimeField('操作时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '对账历史'
        verbose_name_plural = '对账历史'
        ordering = ['-operated_at']
    
    def __str__(self):
        return f"{self.reconciliation} - {self.get_action_display()} - {self.operated_at.strftime('%Y-%m-%d %H:%M')}"

class ReconciliationAttachment(models.Model):
    """对账附件模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reconciliation = models.ForeignKey(ReconciliationRecord, verbose_name='对账记录', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField('附件文件', upload_to='reconciliation_attachments/%Y/%m/')
    file_name = models.CharField('文件名', max_length=255)
    file_size = models.IntegerField('文件大小(KB)')
    uploaded_by = models.ForeignKey(User, verbose_name='上传人', on_delete=models.PROTECT, related_name='uploaded_attachments')
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '对账附件'
        verbose_name_plural = '对账附件'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.reconciliation} - {self.file_name}"
