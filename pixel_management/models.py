from django.db import models
from django.contrib.auth import get_user_model
from task_management.models import Task

# Create your models here.

class Pixel(models.Model):
    AUTHORIZATION_STATUS = (
        (False, '未授权'),
        (True, '已授权'),
    )
    
    id = models.BigAutoField(primary_key=True, verbose_name='ID', help_text='自动生成的ID')
    pixel_id = models.TextField(verbose_name='像素ID', help_text='像素ID，支持超长数字')
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        verbose_name='关联任务', 
        help_text='关联的任务',
        related_name='related_pixels'
    )
    bm_id = models.TextField(verbose_name='BM_ID', help_text='BM_ID，支持多条记录，每行一条')
    account = models.CharField(max_length=200, verbose_name='账单户或单独账户', blank=True, null=True, help_text='账单户或单独账户')
    timezone = models.CharField(max_length=50, verbose_name='账户时区', blank=True, null=True, help_text='账户时区')
    is_authorized = models.BooleanField(default=False, choices=AUTHORIZATION_STATUS, verbose_name='授权状态', help_text='是否授权')
    notes = models.TextField(blank=True, null=True, verbose_name='备注', help_text='备注信息')
    creator = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        verbose_name='创建人',
        help_text='创建该像素的用户',
        related_name='created_pixels',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '像素管理'
        verbose_name_plural = '像素列表'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task.name} - {self.pixel_id}"
