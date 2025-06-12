from django.apps import AppConfig


class ReconciliationManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reconciliation_management"
    verbose_name = "对账管理"
    
    def ready(self):
        import reconciliation_management.signals
