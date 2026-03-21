"""Configuration de l'app documents — enregistrement des signals."""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'documents'
    verbose_name       = 'Gestion documentaire'

    def ready(self):
        import documents.signals  # noqa: F401 — activation des signals
