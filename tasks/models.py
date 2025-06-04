from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from organize.models import Company, Department, User
from django.utils import timezone
import uuid

class Project(models.Model):
    """项目模型"""
    ProjectID = models.AutoField('项目ID', primary_key=True)
    ProjectName = models.CharField('项目名称', max_length=100)
    Description = models.TextField('项目描述', blank=True, null=True)
    StartDate = models.DateField('开始日期', default=timezone.now)
    EndDate = models.DateField('结束日期', null=True, blank=True)
    TimeZone = models.CharField('时区', max_length=50, blank=True, null=True)
    KPI = models.CharField('KPI', max_length=500, blank=True, null=True)
    DailyReportURL = models.URLField('日报链接', max_length=500, blank=True, null=True)
    ProductBackend = models.CharField('产品后台', max_length=200, blank=True, null=True)
    ManagerID = models.ForeignKey(User, verbose_name='项目负责人', on_delete=models.PROTECT)
    CompanyID = models.ForeignKey(Company, verbose_name='所属公司', on_delete=models.PROTECT)
    TaskTypeID = models.ForeignKey('TaskType', verbose_name='任务类型', on_delete=models.PROTECT, null=True, blank=True)
    MediaChannelID = models.ForeignKey('MediaChannel', verbose_name='媒体渠道', on_delete=models.PROTECT, null=True, blank=True)
    Status = models.CharField('项目状态', max_length=20, choices=[
        ('进行中', '进行中'),
        ('已完成', '已完成'),
        ('已暂停', '已暂停'),
    ], default='进行中')
    Status2 = models.ForeignKey('TaskStatus', verbose_name='项目状态2', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        verbose_name = '项目列表'
        verbose_name_plural = '项目列表'
        ordering = ['-StartDate']

    def __str__(self):
        return self.ProjectName

    def clean(self):
        if self.StartDate and self.EndDate and self.StartDate > self.EndDate:
            raise ValidationError({
                'EndDate': _('结束日期必须晚于开始日期。')
            })

class MediaChannel(models.Model):
    """媒体渠道模型"""
    MediaChannelID = models.AutoField('渠道ID', primary_key=True)
    MediaChannelName = models.CharField('渠道名称', max_length=100)
    Description = models.TextField('渠道描述', blank=True)
    CompanyID = models.ForeignKey(Company, verbose_name='所属公司', on_delete=models.PROTECT)

    class Meta:
        verbose_name = '媒体渠道'
        verbose_name_plural = '媒体渠道'
        ordering = ['MediaChannelName']

    def __str__(self):
        return self.MediaChannelName

class TaskType(models.Model):
    """任务类型模型"""
    TaskTypeID = models.AutoField('类型ID', primary_key=True)
    TaskTypeName = models.CharField('类型名称', max_length=100)
    Description = models.TextField('类型描述', blank=True)
    CompanyID = models.ForeignKey(Company, verbose_name='所属公司', on_delete=models.PROTECT)

    class Meta:
        verbose_name = '任务类型'
        verbose_name_plural = '任务类型'
        ordering = ['TaskTypeName']

    def __str__(self):
        return self.TaskTypeName

class TaskStatus(models.Model):
    """任务状态模型"""
    TaskStatusID = models.AutoField('状态ID', primary_key=True)
    TaskStatusName = models.CharField('状态名称', max_length=100)
    Description = models.TextField('状态描述', blank=True)
    CompanyID = models.ForeignKey(Company, verbose_name='所属公司', on_delete=models.PROTECT)

    class Meta:
        verbose_name = '任务状态'
        verbose_name_plural = '任务状态'
        ordering = ['TaskStatusName']

    def __str__(self):
        return self.TaskStatusName
