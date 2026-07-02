import enum
import time
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlencode, urlparse

from django.conf import Settings, settings  # pylint: disable=E0401
from google.auth.transport import requests as google_requests  # pylint: disable=E0401
from google.oauth2 import id_token  # pylint: disable=E0401
from google.oauth2.credentials import Credentials  # pylint: disable=E0401

__all__ = [
    "credentials_to_dict",
    "has_epoch_time_passed",
    "check_gauth_authentication",
    "is_valid_google_url",
    "RedirectionScheme",
    "revoke_google_token",
    "get_credentials",
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


def revoke_google_token(token: str) -> bool:
    """Best-effort revocation of a Google OAuth2 token.

    Revoking a ``refresh_token`` also invalidates the access tokens derived from
    it, so callers should prefer passing the ``refresh_token``.

    Args:
        token: The access or refresh token to revoke.

    Returns:
        bool: True when Google acknowledges the revocation (HTTP 200), False
        otherwise. Network/transport failures are swallowed and reported as
        False so that logout can always proceed to clear the local session.
    """
    if not token:
        return False
    transport = google_requests.Request()
    try:
        response = transport(
            url="https://oauth2.googleapis.com/revoke",
            method="POST",
            body=urlencode({"token": token}).encode("utf-8"),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
    except Exception:  # pylint: disable=broad-exception-caught
        return False
    return getattr(response, "status", None) == 200


def get_credentials(request: Any) -> Optional[Credentials]:
    """Return valid Google credentials for the request, refreshing if needed.

    This is the session-lifecycle accessor: it loads the stored credentials,
    and — when the session has expired but a ``refresh_token`` is available —
    transparently refreshes the access token, re-verifies the fresh ``id_token``
    and writes the refreshed credentials and ``id_info`` back to the session.

    Args:
        request: The Django request whose ``session`` holds the credentials.

    Returns:
        A valid ``Credentials`` object, or ``None`` when the user is not
        authenticated and no refresh is possible.
    """
    session = request.session

    # Fast path: an unexpired session already has usable credentials.
    authenticated, credentials = check_gauth_authentication(session)
    if authenticated:
        return credentials

    # Slow path: attempt a silent refresh using the stored refresh_token.
    credentials_session_key = settings.CREDENTIALS_SESSION_KEY_NAME or "credentials"
    if credentials_session_key not in session:
        return None

    stored = session[credentials_session_key]
    if not stored.get("refresh_token"):
        return None

    credentials = Credentials(
        **stored,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    transport = google_requests.Request()
    try:
        credentials.refresh(transport)
        # A refresh returns a fresh id_token — re-verify it so the cached
        # ``id_info`` (and therefore the session lifetime) moves forward too.
        new_id_info = id_token.verify_oauth2_token(
            id_token=credentials.id_token,
            request=transport,
            audience=settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=5,
        )
    except Exception:  # pylint: disable=broad-exception-caught
        return None

    session[credentials_session_key] = credentials_to_dict(credentials)
    session["id_info"] = new_id_info
    if hasattr(session, "modified"):
        session.modified = True
    return credentials
