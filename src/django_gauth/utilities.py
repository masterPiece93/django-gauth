import enum
import time
from typing import Any, Dict, Tuple, Union
from urllib.parse import urlparse

from django.conf import Settings, settings  # pylint: disable=E0401
from google.oauth2.credentials import Credentials  # pylint: disable=E0401

__all__ = [
    "credentials_to_dict",
    "has_epoch_time_passed",
    "check_gauth_authentication",
    "is_valid_google_url",
    "RedirectionScheme",
]


class RedirectionScheme(str, enum.Enum):
    """Redirection Scheme Options.

    Determines how the login endpoint resolves the final redirect URL
    and what type of HTTP response is returned to the caller.

    Options:
        PRESERVE_ORIGIN_QP: Read origin URL from the ``origin_url`` query
            parameter. Returns a 302 redirect to Google.
        PRESERVE_ORIGIN_HP: Read origin URL from the ``X-ORIGIN-URL`` request
            header. Returns a JsonResponse containing ``redirect_to``.
        LANDING_PAGE: Use the configured ``GOOGLE_AUTH_FINAL_REDIRECT_URL``
            (or the package index). Returns a 302 redirect to Google.
        DEFAULT: Alias for LANDING_PAGE.
    """

    PRESERVE_ORIGIN_QP = "PRESERVE_ORIGIN_QP"
    PRESERVE_ORIGIN_HP = "PRESERVE_ORIGIN_HP"
    LANDING_PAGE = "LANDING_PAGE"
    DEFAULT = "LANDING_PAGE"  # LANDING_PAGE is the default scheme


def credentials_to_dict(credentials: Credentials) -> Dict[str, Any]:
    # ``client_id`` and ``client_secret`` are intentionally omitted so that the
    # OAuth client secret is never persisted in the session backend. They are
    # re-injected from ``settings`` in ``check_gauth_authentication``.
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "scopes": credentials.scopes,
    }


def has_epoch_time_passed(target_epoch_time: Union[int, float]) -> bool:
    """
    Checks if a given epoch time has passed.

    Args:
        target_epoch_time (float or int): The epoch time to check (seconds since epoch).

    Returns:
        bool: True if the target epoch time has passed, False otherwise.
    """
    current_epoch_time = time.time()
    return target_epoch_time <= current_epoch_time


def check_gauth_authentication(session: Settings) -> Tuple[bool, object]:
    """
    checks if authentication session still valid
    """
    credentials_session_key = settings.CREDENTIALS_SESSION_KEY_NAME or "credentials"

    if credentials_session_key not in session:
        return False, None

    # Load credentials from the session, re-injecting the client_id/secret from
    # settings (they are never persisted in the session store, see ISSUE-2).
    credentials = Credentials(
        **session[credentials_session_key],
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )

    if not credentials.valid:
        return False, None

    if "id_info" in session and has_epoch_time_passed(session["id_info"]["exp"]):
        return False, None

    return True, credentials


def is_valid_google_url(url: str) -> bool:
    VALID_SCHEME = "https"  # pylint: disable=C0103
    VALID_DOMAIN = "docs.google.com"  # pylint: disable=C0103
    try:
        result = urlparse(url)
        return (
            all([result.scheme, result.netloc])
            and result.scheme == VALID_SCHEME
            and result.netloc == VALID_DOMAIN
        )
    except ValueError:
        return False
