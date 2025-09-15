from django.apps import AppConfig   # pylint: disable=E0401

# pylint: disable=R0903
class DjangoGauthConfig(AppConfig):
    """
    App Configurator @ django_gauth
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_gauth"
