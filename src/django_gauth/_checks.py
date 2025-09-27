# myapp/checks.py
import logging
from enum import Enum
from typing import Any, Callable

from django.conf import settings  # pylint: disable=E0401
from django.core.checks import Error  # pylint: disable=E0401

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
    E004 = (
        "INVALID_GAUTH_SCOPE",
        "Please set valid oauth2 SCOPE"
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
                "GOOGLE_CLIENT_ID is not defined in settings."\
                +   f"Required for app:{__app_label__} to work.",
                hint="Define GOOGLE_CLIENT_ID in your project settings.py",
                id=formulate_check_id(ErrorCodes.E003.name),
            )
        )
    if not hasattr(settings, "GOOGLE_CLIENT_SECRET"):
        errors.append(
            Error(
                "GOOGLE_CLIENT_SECRET is not defined in settings."\
                +   f"Required for app:{__app_label__} to work.",
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
                "Django SessionMiddleware is not included in settings. "\
                    +   "Required for app:{__app_label__} to work.",
                hint=f"Define {session_middleware_path} in your "\
                    +   "project`s MIDDLEWARE variable in settings.py",
                id=formulate_check_id(ErrorCodes.E002.name),
            )
        )
    return errors
