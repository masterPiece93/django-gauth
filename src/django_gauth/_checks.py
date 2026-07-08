# myapp/checks.py
import logging
from enum import Enum
from typing import Any, Callable

from django.conf import settings  # pylint: disable=E0401
from django.core.checks import Error  # pylint: disable=E0401
from django.core.checks import Warning as SysCheckWarning  # pylint: disable=E0401

from django_gauth import defaults

logger = logging.getLogger(__name__)

__app_label__ = "django_gauth"


class ErrorCodes(Enum):
    """Error Codes for app checks"""

    E001 = ("MISSING_REQUIRED_SETTINGS", "Please define the required project settings")
    E002 = (
        "MISSING_REQUIRED_MIDDLEWARE",
        "Please include required middleware in settings",
    )
    E003 = (
        "MISSING_REQUIRED_GOOGLE_CREDENTIALS",
        "Please include required google oauth2 web client \
        credentials ( GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET )",
    )
    E004 = ("INVALID_GAUTH_SCOPE", "Please set valid oauth2 SCOPE")
    W001 = (
        "MISSING_AUTH_APP_FOR_USER_INTEGRATION",
        "django.contrib.auth is required when GOOGLE_USER_INTEGRATION is enabled",
    )
    W002 = (
        "MISSING_AUTH_MIDDLEWARE_FOR_USER_INTEGRATION",
        "AuthenticationMiddleware is required when GOOGLE_USER_INTEGRATION is enabled",
    )
    W003 = (
        "MISSING_AUTH_BACKEND_FOR_USER_INTEGRATION",
        "GoogleAuthBackend is required when GOOGLE_USER_INTEGRATION is enabled",
    )


formulate_check_id: Callable = lambda code: f"{__app_label__}.{code}"


def check_project_settings(
    app_configs: object, **kwargs: Any  # pylint: disable=W0613
) -> list:
    errors = []
    if not hasattr(settings, "SECRET_KEY"):
        errors.append(
            Error(
                "SECRET_KEY setting not defined. Required for app:{__app_label__} to work.",
                hint="Define SECRET_KEY in your project settings.py",
                id=formulate_check_id(ErrorCodes.E001.name),
            )
        )
    if not hasattr(settings, "GOOGLE_CLIENT_ID"):
        errors.append(
            Error(
                "GOOGLE_CLIENT_ID is not defined in settings."
                + f"Required for app:{__app_label__} to work.",
                hint="Define GOOGLE_CLIENT_ID in your project settings.py",
                id=formulate_check_id(ErrorCodes.E003.name),
            )
        )
    if not hasattr(settings, "GOOGLE_CLIENT_SECRET"):
        errors.append(
            Error(
                "GOOGLE_CLIENT_SECRET is not defined in settings."
                + f"Required for app:{__app_label__} to work.",
                hint="Define GOOGLE_CLIENT_SECRET in your project settings.py",
                id=formulate_check_id(ErrorCodes.E003.name),
            )
        )

    return errors


def check_project_middlewares(
    app_configs: object, **kwargs: Any  # pylint: disable=W0613
) -> list:
    errors = []

    session_middleware_path = "django.contrib.sessions.middleware.SessionMiddleware"

    if not session_middleware_path in settings.MIDDLEWARE:
        errors.append(
            Error(
                "Django SessionMiddleware is not included in settings. "
                + "Required for app:{__app_label__} to work.",
                hint=f"Define {session_middleware_path} in your "
                + "project`s MIDDLEWARE variable in settings.py",
                id=formulate_check_id(ErrorCodes.E002.name),
            )
        )
    return errors


def check_user_integration_requirements(
    app_configs: object, **kwargs: Any  # pylint: disable=W0613
) -> list:
    """Verify the project wiring when Django User integration is switched on.

    ``GOOGLE_USER_INTEGRATION`` is opt-in and inert by default, so these are
    Warnings (not Errors): the core Google/SPA flow keeps working, but
    ``request.user`` will silently stay ``AnonymousUser`` unless all three
    moving parts below are present. Surfacing them via ``manage.py check`` turns
    a confusing silent no-op into an actionable message.
    """
    warnings_list: list = []

    integration_enabled = getattr(
        settings,
        "GOOGLE_USER_INTEGRATION",
        defaults.GOOGLE_USER_INTEGRATION,
    )
    if not integration_enabled:
        return warnings_list

    # 1. The auth app supplies the User model, ModelBackend and login/logout.
    if "django.contrib.auth" not in getattr(settings, "INSTALLED_APPS", []):
        warnings_list.append(
            SysCheckWarning(
                "GOOGLE_USER_INTEGRATION is enabled but 'django.contrib.auth' "
                "is missing from INSTALLED_APPS.",
                hint="Add 'django.contrib.auth' to INSTALLED_APPS.",
                id=formulate_check_id(ErrorCodes.W001.name),
            )
        )

    # 2. AuthenticationMiddleware is what attaches request.user per request.
    auth_middleware_path = "django.contrib.auth.middleware.AuthenticationMiddleware"
    if auth_middleware_path not in getattr(settings, "MIDDLEWARE", []):
        warnings_list.append(
            SysCheckWarning(
                "GOOGLE_USER_INTEGRATION is enabled but "
                f"'{auth_middleware_path}' is missing from MIDDLEWARE.",
                hint=(
                    f"Add '{auth_middleware_path}' to MIDDLEWARE, "
                    "after SessionMiddleware."
                ),
                id=formulate_check_id(ErrorCodes.W002.name),
            )
        )

    # 3. GoogleAuthBackend is what turns a verified id_info into a User.
    backend_path = "django_gauth.backends.GoogleAuthBackend"
    if backend_path not in getattr(settings, "AUTHENTICATION_BACKENDS", []):
        warnings_list.append(
            SysCheckWarning(
                "GOOGLE_USER_INTEGRATION is enabled but "
                f"'{backend_path}' is missing from AUTHENTICATION_BACKENDS.",
                hint=(
                    f"Add '{backend_path}' to AUTHENTICATION_BACKENDS "
                    "(keep 'django.contrib.auth.backends.ModelBackend' too)."
                ),
                id=formulate_check_id(ErrorCodes.W003.name),
            )
        )

    return warnings_list
