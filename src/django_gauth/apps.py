import warnings
from typing import Any, Dict
from urllib.parse import urlparse

from django.apps import AppConfig  # pylint: disable=E0401

# pylint: disable=E0602
from django.conf import settings  # pylint: disable=E0401
from django.core.checks import Info  # pylint: disable=E0401
from django.core.checks import register  # pylint: disable=E0401
from django.core.checks import Tags as DjangoTags  # pylint: disable=E0401
from django.core.checks import Warning as SysCheckWarning  # pylint: disable=E0401

from django_gauth import defaults
from django_gauth._checks import (
    ErrorCodes,
    check_project_middlewares,
    check_project_settings,
    check_user_integration_requirements,
    formulate_check_id,
)


def is_url(url_string: str) -> bool:
    """Check if a string is a valid URL.
    [utility function]"""
    try:
        result = urlparse(url_string)
        # Returns True if both scheme (e.g., http) and netloc (e.g., github.com) exist
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


warnings.simplefilter("default")


# pylint: disable=R0903
class Tags(DjangoTags):
    """Extending with Custom Tags

    NOTE : Do this if none of the existing tags work for you:
    https://docs.djangoproject.com/en/3.1/ref/checks/#builtin-tags
    """

    django_gauth_compatibility = "django_gauth_compatibility"


def apply_setting_defaults() -> None:
    """Populate django-gauth's optional settings with their packaged defaults.

    This runs from :meth:`DjangoGauthConfig.ready`, which Django executes during
    ``django.setup()`` for **every** entrypoint — ``runserver``, ``gunicorn``,
    ``uwsgi``, ASGI servers, and management commands alike. That is what makes
    these defaults reliable in production.

    Historically the defaults were applied inside :func:`set_defaults`, a
    *system check*. But Django only runs system checks for a handful of
    management commands (``check``, ``runserver``, ``migrate`` …) — **never**
    when a WSGI/ASGI server merely imports the application object. Under
    ``gunicorn``/``uwsgi`` the checks (and therefore the defaults) never ran, so
    runtime code that reads e.g. ``settings.SCOPE`` or ``settings.STATE_KEY_NAME``
    directly could raise ``AttributeError``. Applying them here fixes that for
    every server.

    Idempotent: only settings that are *absent* are filled; anything the project
    already defines is left untouched (and is still validated by
    :func:`set_defaults` when the check framework runs).
    """
    setting_defaults: Dict[str, Any] = {
        "SCOPE": [],
        "GOOGLE_AUTH_FINAL_REDIRECT_URL": defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL,
        "CREDENTIALS_SESSION_KEY_NAME": defaults.CREDENTIALS_SESSION_KEY_NAME,
        "STATE_KEY_NAME": defaults.STATE_KEY_NAME,
        "FINAL_REDIRECT_KEY_NAME": defaults.FINAL_REDIRECT_KEY_NAME,
        "GOOGLE_LOGIN_PROMPT": defaults.GOOGLE_LOGIN_PROMPT,
    }
    for name, value in setting_defaults.items():
        if not hasattr(settings, name):
            setattr(settings, name, value)


# pylint: disable=R0903
class DjangoGauthConfig(AppConfig):
    """
    App Configurator @ django_gauth
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_gauth"

    def ready(self) -> None:
        # Apply setting defaults here — not only via the ``set_defaults`` system
        # check — so they are present under EVERY server (gunicorn/uwsgi/asgi
        # included). Django does not run system checks when a WSGI/ASGI server
        # imports the application object, so relying on the check alone left the
        # defaults unset in production (see apply_setting_defaults docstring).
        apply_setting_defaults()
        register(Tags.compatibility)(check_project_middlewares)
        register(Tags.django_gauth_compatibility)(check_project_settings)
        register(Tags.django_gauth_compatibility)(check_user_integration_requirements)


@register(Tags.django_gauth_compatibility)
def set_defaults(app_configs: object, **kwargs: Any) -> list:  # pylint: disable=W0613
    errors = []
    if not hasattr(settings, "SCOPE"):
        setattr(settings, "SCOPE", [])
        errors.append(
            SysCheckWarning(
                "SCOPE setting is not defined. Defaulting to `[]`."
                + "It may affect the normal flow of oauth and might not run as expected."
                + "Please rectify ASAP.",
                hint=(
                    "See https://masterpiece93.github.io/django-gauth/settings/ "
                    + "for more information."
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
        _msg = (
            "GOOGLE_AUTH_FINAL_REDIRECT_URL settings is not defined."
            + f"Defaulting to `{defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL}`"
        )
        warnings.warn(_msg)
    else:
        if settings.GOOGLE_AUTH_FINAL_REDIRECT_URL and (
            not len(settings.GOOGLE_AUTH_FINAL_REDIRECT_URL) > 0
            or not is_url(settings.GOOGLE_AUTH_FINAL_REDIRECT_URL)
        ):
            _msg = (
                "GOOGLE_AUTH_FINAL_REDIRECT_URL setting is set to"
                + f"`{settings.GOOGLE_AUTH_FINAL_REDIRECT_URL}` which is logically incorrect."
            )
            info = Info(_msg)
            errors.append(info)
    if not hasattr(settings, "CREDENTIALS_SESSION_KEY_NAME"):
        setattr(
            settings,
            "CREDENTIALS_SESSION_KEY_NAME",
            defaults.CREDENTIALS_SESSION_KEY_NAME,
        )
        _msg = (
            "CREDENTIALS_SESSION_KEY_NAME settings is not defined."
            + "Defaulting to `{defaults.CREDENTIALS_SESSION_KEY_NAME}`"
        )
        warnings.warn(_msg)
    else:
        if not settings.CREDENTIALS_SESSION_KEY_NAME:
            _msg = (
                "CREDENTIALS_SESSION_KEY_NAME setting is set to"
                + "`{settings.CREDENTIALS_SESSION_KEY_NAME}` which is logically incorrect."
            )
            info = Info(_msg)
            errors.append(info)
    if not hasattr(settings, "STATE_KEY_NAME"):
        setattr(settings, "STATE_KEY_NAME", defaults.STATE_KEY_NAME)
        _msg = (
            "STATE_KEY_NAME settings is not defined."
            + "Defaulting to `{defaults.STATE_KEY_NAME}`"
        )
        warnings.warn(_msg)
    else:
        if not settings.STATE_KEY_NAME:
            _msg = (
                f"STATE_KEY_NAME setting is set to `{settings.STATE_KEY_NAME}`"
                + "which is logically incorrect."
            )
            info = Info(_msg)
            errors.append(info)

    if not hasattr(settings, "FINAL_REDIRECT_KEY_NAME"):
        setattr(settings, "FINAL_REDIRECT_KEY_NAME", defaults.FINAL_REDIRECT_KEY_NAME)
        _msg = (
            "FINAL_REDIRECT_KEY_NAME settings is not defined."
            + f"Defaulting to `{defaults.FINAL_REDIRECT_KEY_NAME}`"
        )
        warnings.warn(_msg)
    else:
        if not settings.FINAL_REDIRECT_KEY_NAME:
            _msg = (
                "FINAL_REDIRECT_KEY_NAME setting is set to"
                + f"`{settings.FINAL_REDIRECT_KEY_NAME}` which is logically incorrect."
            )
            info = Info(_msg)
            errors.append(info)

    if not hasattr(settings, "GOOGLE_LOGIN_PROMPT"):
        setattr(settings, "GOOGLE_LOGIN_PROMPT", defaults.GOOGLE_LOGIN_PROMPT)
        _msg = (
            "GOOGLE_LOGIN_PROMPT settings is not defined."
            + f"Defaulting to `{defaults.GOOGLE_LOGIN_PROMPT}`"
        )
        warnings.warn(_msg)
    else:
        if not settings.GOOGLE_LOGIN_PROMPT:
            _msg = (
                "GOOGLE_LOGIN_PROMPT setting is set to"
                + f"`{settings.GOOGLE_LOGIN_PROMPT}` which is logically incorrect."
            )
            info = Info(_msg)
            errors.append(info)
    return errors
