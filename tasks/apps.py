from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tasks"
    verbose_name = "项目管理"

    def ready(self):
        # 导入信号处理器
        import tasks.signals
