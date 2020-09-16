from django.apps import AppConfig


class EasyAuditConfig(AppConfig):
    name = "audit"
    verbose_name = "Easy Audit Application"

    def ready(self):
        from audit.signals import auth_signals, model_signals, request_signals
