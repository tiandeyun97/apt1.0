# Generated by Django 5.1.4 on 2025-03-27 07:22

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0002_alter_project_options_project_pixel"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="Pixel",
        ),
    ]
