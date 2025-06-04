from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('task_management', '0001_initial'),
        ('pixel_management', '0001_initial'),
    ]

    operations = [
        # 修改字段类型
        migrations.AlterField(
            model_name='pixel',
            name='pixel_id',
            field=models.BigIntegerField(help_text='像素ID', verbose_name='像素ID'),
        ),
        migrations.AlterField(
            model_name='pixel',
            name='bm_id',
            field=models.BigIntegerField(help_text='BM_ID', verbose_name='BM_ID'),
        ),
        
        # 添加创建人字段
        migrations.AddField(
            model_name='pixel',
            name='creator',
            field=models.ForeignKey(
                blank=True,
                help_text='创建该像素的用户',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_pixels',
                to=settings.AUTH_USER_MODEL,
                verbose_name='创建人'
            ),
        ),
        
        # 移除任务名称字段，添加任务外键
        migrations.RemoveField(
            model_name='pixel',
            name='task_name',
        ),
        migrations.AddField(
            model_name='pixel',
            name='task',
            field=models.ForeignKey(
                default=None,
                help_text='关联的任务',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='related_pixels',
                to='task_management.task',
                verbose_name='关联任务'
            ),
            preserve_default=False,
        ),
    ] 