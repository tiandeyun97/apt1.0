from django.db import models
from django.utils import timezone
import uuid
from tasks.models import Project, TaskStatus
from organize.models import Company, User
import re

class Task(models.Model):
    """任务模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('任务名称', max_length=200)
    advert_name = models.CharField('广告命名', max_length=200)
    project = models.ForeignKey(Project, verbose_name='所属项目', on_delete=models.PROTECT)
    product_info = models.TextField('产品信息', blank=True)
    status = models.ForeignKey(TaskStatus, verbose_name='任务状态', on_delete=models.PROTECT)
    backend = models.CharField('产品后台', max_length=500, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    start_date = models.DateField('开始日期', default=timezone.now, blank=True, null=True)
    end_date = models.DateField('结束日期', null=True, blank=True)
    notes = models.TextField('备注信息', blank=True)
    pixel = models.TextField('广告像素', blank=True, null=True, help_text='广告像素代码')
    publish_url = models.URLField('投放链接', max_length=500, blank=True, null=True, help_text='广告投放链接')
    company = models.ForeignKey(Company, verbose_name='所属公司', on_delete=models.PROTECT)
    timezone = models.CharField('时区', max_length=50, blank=True, null=True, help_text='任务所在时区')
    optimizer = models.ManyToManyField(
        User, 
        verbose_name='优化师', 
        related_name='optimized_tasks',
        blank=True
    )
    sort_number = models.IntegerField('排序数字', default=0, help_text='从任务名称中提取的数字，用于排序')
    
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务列表'
        ordering = ['-sort_number', '-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils.translation import gettext_lazy as _
        
        # 验证结束日期必须晚于开始日期
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': _('结束日期必须晚于开始日期。')
            })
    
    def save(self, *args, **kwargs):
        # 从任务名称中提取排序数字
        if self.name:
            # 使用正则表达式从名称中提取最后一个连字符后的数字
            match = re.search(r'-(\d+)$', self.name)
            if match:
                self.sort_number = int(match.group(1))
            else:
                # 如果没有匹配到特定模式，尝试提取任何数字作为备选
                numbers = re.findall(r'\d+', self.name)
                if numbers:
                    self.sort_number = int(numbers[-1])
        
        super().save(*args, **kwargs)
