from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Project
from task_management.models import Task
from task_management.views import decode_unicode_escapes

@receiver(pre_save, sender=Project)
def store_original_status2(sender, instance, **kwargs):
    """
    在保存项目前存储原始的Status2值
    """
    # 如果是已存在的项目，存储原始Status2值
    if instance.pk:
        try:
            original_instance = Project.objects.get(pk=instance.pk)
            # 在实例上存储原始Status2值
            instance._original_status2_id = original_instance.Status2_id
            # 存储原始时区值
            instance._original_timezone = original_instance.TimeZone
        except Project.DoesNotExist:
            # 如果是新创建的项目，设置原始值为None
            instance._original_status2_id = None
            instance._original_timezone = None
    else:
        # 如果是新创建的项目，设置原始值为None
        instance._original_status2_id = None
        instance._original_timezone = None

@receiver(post_save, sender=Project)
def update_tasks_status(sender, instance, created, **kwargs):
    """
    当项目的Status2字段值变为6时，将所有关联的任务状态更新为相同的状态
    """
    # 如果是新创建的项目且Status2为6
    if created and instance.Status2_id == 6:
        Task.objects.filter(project=instance).update(status=instance.Status2)
        return
    
    # 如果是更新项目且Status2发生变化为6
    if not created and hasattr(instance, '_original_status2_id'):
        # 检查Status2是否发生变化且新值为6
        if instance._original_status2_id != instance.Status2_id and instance.Status2_id == 6:
            # 更新所有关联任务的状态
            Task.objects.filter(project=instance).update(status=instance.Status2)

@receiver(post_save, sender=Project)
def update_tasks_timezone(sender, instance, created, **kwargs):
    """
    将项目的时区同步到所有关联任务的时区
    """
    # 如果是新创建的项目，不需要做任何操作，因为还没有关联的任务
    if created:
        return
    
    # 检查时区是否发生变化
    if hasattr(instance, '_original_timezone') and instance._original_timezone != instance.TimeZone:
        # 解码项目时区值
        timezone = decode_unicode_escapes(instance.TimeZone) if instance.TimeZone else None
        original_timezone = decode_unicode_escapes(instance._original_timezone) if instance._original_timezone else None
        
        # 更新所有关联任务的时区（仅更新时区为空或与原始项目时区相同的任务）
        Task.objects.filter(project=instance).filter(
            timezone__isnull=True
        ).update(timezone=timezone)
        
        # 更新那些时区与项目原时区相同的任务，这意味着它们可能是跟随项目时区的
        if original_timezone:  # 确保原时区不是None
            Task.objects.filter(
                project=instance, 
                timezone=original_timezone
            ).update(timezone=timezone)

@receiver(pre_save, sender=Task)
def set_task_timezone_from_project(sender, instance, **kwargs):
    """
    当创建新任务时，如果时区为空，则从关联项目获取时区
    """
    # 只在任务时区为空时同步项目时区
    if not instance.timezone and instance.project_id:
        try:
            project = Project.objects.get(pk=instance.project_id)
            # 解码项目时区值
            instance.timezone = decode_unicode_escapes(project.TimeZone) if project.TimeZone else None
        except Project.DoesNotExist:
            pass