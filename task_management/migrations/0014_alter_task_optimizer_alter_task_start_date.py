# Generated by Django 5.0.1 on 2025-05-23 06:28

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("task_management", "0013_recreate_task_optimizer_table"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="optimizer",
            field=models.ManyToManyField(
                blank=True,
                related_name="optimized_tasks",
                to=settings.AUTH_USER_MODEL,
                verbose_name="优化师",
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="start_date",
            field=models.DateField(
                blank=True,
                default=django.utils.timezone.now,
                null=True,
                verbose_name="开始日期",
            ),
        ),
    ]
