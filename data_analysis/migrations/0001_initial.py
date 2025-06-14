# Generated by Django 5.0.1 on 2025-05-23 06:28

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("consumption_management", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConsumptionAnalysis",
            fields=[],
            options={
                "verbose_name": "消耗趋势分析",
                "verbose_name_plural": "消耗趋势分析",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("consumption_management.taskconsumption",),
        ),
        migrations.CreateModel(
            name="OptimizerRanking",
            fields=[],
            options={
                "verbose_name": "优化师榜单排名",
                "verbose_name_plural": "优化师榜单排名",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("consumption_management.taskconsumption",),
        ),
    ]
