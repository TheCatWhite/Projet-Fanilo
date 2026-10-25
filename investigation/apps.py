from django.apps import AppConfig


class InvestigationConfig(AppConfig):
    """Configuration de l'application d'investigation journalistique."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "investigation"
    verbose_name = "Investigation FactCheck Mada"
