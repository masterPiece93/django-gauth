import warnings
from typing import Any

from django.apps import AppConfig  # pylint: disable=E0401

# pylint: disable=E0602
from django.conf import settings  # pylint: disable=E0401
from django.core.checks import Info  # pylint: disable=E0401
from django.core.checks import register  # pylint: disable=E0401
from django.core.checks import Tags as DjangoTags  # pylint: disable=E0401
from django.core.checks import Warning as SysCheckWarning  # pylint: disable=E0401

from django_gauth import defaults
from django_gauth._checks import (
    check_project_middlewares,
    check_project_settings,
    formulate_check_id,
    ErrorCodes
)

warnings.simplefilter("default")


# pylint: disable=R0903
class Tags(DjangoTags):
    """Extending with Custom Tags

    NOTE : Do this if none of the existing tags work for you:
    https://docs.djangoproject.com/en/3.1/ref/checks/#builtin-tags
    """

    django_gauth_compatibility = "django_gauth_compatibility"


# pylint: disable=R0903
class DjangoGauthConfig(AppConfig):
    """
    App Configurator @ django_gauth
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_gauth"

    def ready(self) -> None:
        register(Tags.compatibility)(check_project_middlewares)
        register(Tags.django_gauth_compatibility)(check_project_settings)


@register(Tags.django_gauth_compatibility)
def set_defaults(
    app_configs: object, **kwargs: Any  # pylint: disable=W0613
) -> list:
    errors = []
    if not hasattr(settings, "SCOPE"):
        setattr(settings, "SCOPE", [])
        errors.append(
            SysCheckWarning(
                "SCOPE setting is not defined. Defaulting to `[]`."\
                +   "It may affect the normal flow of oauth and might not run as expected."\
                +   "Please rectify ASAP.",
                hint=(
                    "See https://masterpiece93.github.io/django-gauth/settings/ "\
                    +   "for more information."
                ),
                id=formulate_check_id(ErrorCodes.E004.name),
            )
        )

    if not hasattr(settings, "GOOGLE_AUTH_FINAL_REDIRECT_URL"):
        setattr(
            settings,
            "GOOGLE_AUTH_FINAL_REDIRECT_URL",
            defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL,
        )
        _msg = "GOOGLE_AUTH_FINAL_REDIRECT_URL settings is not defined."\
        +f"Defaulting to `{defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL}`"
        warnings.warn(_msg)
    else:
        if not settings.GOOGLE_AUTH_FINAL_REDIRECT_URL:
            _msg = "GOOGLE_AUTH_FINAL_REDIRECT_URL setting is set to"\
            +   f"`{settings.GOOGLE_AUTH_FINAL_REDIRECT_URL}` which is logically incorrect."
            info = Info(_msg)
            errors.append(info)
    if not hasattr(settings, "CREDENTIALS_SESSION_KEY_NAME"):
        setattr(
            settings,
            "CREDENTIALS_SESSION_KEY_NAME",
            defaults.CREDENTIALS_SESSION_KEY_NAME,
        )
        _msg = "CREDENTIALS_SESSION_KEY_NAME settings is not defined."\
        +   "Defaulting to `{defaults.CREDENTIALS_SESSION_KEY_NAME}`"
        warnings.warn(_msg)
    else:
        if not settings.CREDENTIALS_SESSION_KEY_NAME:
            _msg = "CREDENTIALS_SESSION_KEY_NAME setting is set to"\
            +   "`{settings.CREDENTIALS_SESSION_KEY_NAME}` which is logically incorrect."
            info = Info(_msg)
            errors.append(info)
    if not hasattr(settings, "STATE_KEY_NAME"):
        setattr(settings, "STATE_KEY_NAME", defaults.STATE_KEY_NAME)
        _msg = "STATE_KEY_NAME settings is not defined."\
        +   "Defaulting to `{defaults.STATE_KEY_NAME}`"
        warnings.warn(_msg)
    else:
        if not settings.STATE_KEY_NAME:
            _msg = f"STATE_KEY_NAME setting is set to `{settings.STATE_KEY_NAME}`"\
            +   "which is logically incorrect."
            info = Info(_msg)
            errors.append(info)

    if not hasattr(settings, "FINAL_REDIRECT_KEY_NAME"):
        setattr(
            settings, "FINAL_REDIRECT_KEY_NAME", defaults.FINAL_REDIRECT_KEY_NAME
        )
        _msg = "FINAL_REDIRECT_KEY_NAME settings is not defined."\
        +   "Defaulting to `{defaults.FINAL_REDIRECT_KEY_NAME}`"
        warnings.warn(_msg)
    else:
        if not settings.FINAL_REDIRECT_KEY_NAME:
            _msg = "FINAL_REDIRECT_KEY_NAME setting is set to"\
            +   "`{settings.FINAL_REDIRECT_KEY_NAME}` which is logically incorrect."
            info = Info(_msg)
            errors.append(info)
    return errors
