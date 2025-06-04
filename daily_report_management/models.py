from django.db import models
from django.utils import timezone
from decimal import Decimal
from task_management.models import Task
from django.db.models import Q

class DailyReport(models.Model):
    """日报管理模型，记录每日渠道数据"""
    id = models.AutoField('ID', primary_key=True, editable=False)
    date = models.DateField('日期', default=timezone.now)
    channel_name = models.CharField('渠道名称', max_length=100)
    consumption = models.DecimalField('消耗', max_digits=10, decimal_places=2, default=0)
    registrations = models.IntegerField('注册人数', default=0)
    first_deposits = models.IntegerField('首充人数', default=0)
    budget = models.DecimalField('预算', max_digits=10, decimal_places=2, default=0)
    kpi = models.CharField('KPI', max_length=255, blank=True, null=True)
    budget_description = models.TextField('预算说明', blank=True, null=True)
    daily_recharge_rate = models.DecimalField('当日复充率', max_digits=5, decimal_places=2, default=0)
    retention_day2 = models.DecimalField('二日留存', max_digits=5, decimal_places=2, default=0)
    retention_day3 = models.DecimalField('三日留存', max_digits=5, decimal_places=2, default=0)
    retention_day4 = models.DecimalField('四日留存', max_digits=5, decimal_places=2, default=0)
    retention_day5 = models.DecimalField('五日留存', max_digits=5, decimal_places=2, default=0)
    retention_day7 = models.DecimalField('七日留存', max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '日报数据'
        verbose_name_plural = '日报数据'
        ordering = ['-date', 'channel_name']
        unique_together = ['date', 'channel_name']  # 确保每个渠道每天只有一条记录
        
    def __str__(self):
        return f"{self.date} - {self.channel_name}"
    
    @property
    def registration_cost(self):
        """计算注册成本"""
        if self.registrations and self.registrations > 0:
            return self.consumption / self.registrations
        return Decimal('0.00')
    
    @property
    def first_deposit_cost(self):
        """计算首充成本"""
        if self.first_deposits and self.first_deposits > 0:
            return self.consumption / self.first_deposits
        return Decimal('0.00')
        
    @property
    def optimizers(self):
        """
        获取此渠道对应的优化师
        使用channel_name查询任务，获取相关联的优化师用户名
        """
        # 查找与channel_name匹配的任务
        tasks = Task.objects.filter(
            Q(name__icontains=self.channel_name) | 
            Q(advert_name__icontains=self.channel_name)
        ).distinct()
        
        # 获取所有相关任务的优化师
        optimizer_names = set()  # 使用集合避免重复
        for task in tasks:
            for optimizer in task.optimizer.all():
                if optimizer.username and optimizer.username.strip():  # 确保用户名不为空
                    optimizer_names.add(optimizer.username.strip())
        
        # 返回优化师列表字符串，以逗号分隔
        if optimizer_names:
            return ', '.join(sorted(optimizer_names))  # 排序后返回，保证顺序一致
        return '-'
