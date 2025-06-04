from django.db import models
from consumption_management.models import TaskConsumption

# Create your models here.

class ConsumptionAnalysis(TaskConsumption):
    """
    消费分析模型 - 这是一个代理模型，不创建新表
    用于在admin中显示消费趋势分析
    """
    class Meta:
        proxy = True
        verbose_name = '消耗趋势分析'
        verbose_name_plural = verbose_name

class OptimizerRanking(TaskConsumption):
    """
    优化师排名模型 - 这是一个代理模型，不创建新表
    用于在admin中显示优化师榜单排名
    """
    class Meta:
        proxy = True
        verbose_name = '优化师榜单排名'
        verbose_name_plural = verbose_name
