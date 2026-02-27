from django.apps import AppConfig


class TrainingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.training'
    verbose_name = 'Risk Scoring & Remediation Training'

    def ready(self):
        # Import signals when app is ready
        import apps.training.signals  # noqa: F401
