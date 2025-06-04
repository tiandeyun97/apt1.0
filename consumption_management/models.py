from django.db import models
from task_management.models import Task
from organize.models import User
import uuid
    
class TaskConsumption(models.Model):
    """任务消耗记录模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, verbose_name='关联任务', on_delete=models.CASCADE, related_name='consumptions')
    creator = models.ForeignKey(User, verbose_name='创建人', on_delete=models.PROTECT, related_name='created_consumptions', null=True, blank=True)
    date = models.DateField('日期')
    daily_consumption = models.DecimalField('当日消耗', max_digits=10, decimal_places=2)
    return_flow = models.DecimalField('回流', max_digits=10, decimal_places=2, default=0, blank=True)
    actual_consumption = models.DecimalField('实际消耗', max_digits=10, decimal_places=2, editable=False)
    registrations = models.IntegerField('注册人数', default=0, blank=True)
    first_deposits = models.IntegerField('首充人数', default=0, blank=True)
    impressions = models.IntegerField('展示量', default=0, blank=True)
    clicks = models.IntegerField('点击量', default=0, blank=True)
    return_flow_ratio = models.DecimalField('回流占比', max_digits=5, decimal_places=2, editable=False)
    click_conversion_rate = models.DecimalField('点击转化率', max_digits=5, decimal_places=2, editable=False)
    registration_conversion_rate = models.DecimalField('注册转化率', max_digits=5, decimal_places=2, editable=False)
    registration_cost = models.DecimalField('注册成本', max_digits=10, decimal_places=2, editable=False)
    first_deposit_conversion_rate = models.DecimalField('首充转化率', max_digits=5, decimal_places=2, editable=False)
    first_deposit_cost = models.DecimalField('首充成本', max_digits=10, decimal_places=2, editable=False)
    click_cost = models.DecimalField('点击成本', max_digits=10, decimal_places=2, editable=False)
    ecpm = models.DecimalField('ECPM', max_digits=10, decimal_places=2, editable=False, help_text='每千次展示收益')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '消耗明细'
        verbose_name_plural = '消耗明细'

    def save(self, *args, **kwargs):
        # 计算实际消耗
        self.actual_consumption = self.daily_consumption + self.return_flow
        
        # 计算回流占比
        if self.daily_consumption:
            self.return_flow_ratio = (self.return_flow / self.daily_consumption) * 100
        else:
            self.return_flow_ratio = 0
            
        # 计算点击转化率
        if self.impressions:
            self.click_conversion_rate = (self.clicks / self.impressions) * 100
        else:
            self.click_conversion_rate = 0
            
        # 计算注册转化率
        if self.clicks:
            self.registration_conversion_rate = (self.registrations / self.clicks) * 100
        else:
            self.registration_conversion_rate = 0
            
        # 计算注册成本
        if self.registrations:
            self.registration_cost = self.actual_consumption / self.registrations
        else:
            self.registration_cost = 0
            
        # 计算首充转化率
        if self.registrations:
            self.first_deposit_conversion_rate = (self.first_deposits / self.registrations) * 100
        else:
            self.first_deposit_conversion_rate = 0
            
        # 计算首充成本
        if self.first_deposits:
            self.first_deposit_cost = self.actual_consumption / self.first_deposits
        else:
            self.first_deposit_cost = 0
            
        # 计算点击成本
        if self.clicks:
            self.click_cost = self.actual_consumption / self.clicks
        else:
            self.click_cost = 0
            
        # 计算ECPM（每千次展示收益）
        if self.impressions:
            self.ecpm = (self.actual_consumption / self.impressions) * 1000
        else:
            self.ecpm = 0
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task.name} - {self.date}"