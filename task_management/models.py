from django.db import models
from django.utils import timezone
import uuid
from tasks.models import Project, TaskStatus
from organize.models import Company, User

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
    
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务列表'
        ordering = ['-created_at']
    
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
