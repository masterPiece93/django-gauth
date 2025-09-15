import time
from typing import Any, Dict, Tuple, Union
from urllib.parse import urlparse

from django.conf import Settings, settings          # pylint: disable=E0401
from google.oauth2.credentials import Credentials   # pylint: disable=E0401

__all__ = [
    "credentials_to_dict",
    "has_epoch_time_passed",
    "check_gauth_authentication",
    "is_valid_google_url",
]


def credentials_to_dict(credentials: Credentials) -> Dict[str, Any]:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
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

    # Load credentials from the session.
    credentials = Credentials(**session[credentials_session_key])

    if not credentials.valid:
        return False, None

    if "id_info" in session and has_epoch_time_passed(session["id_info"]["exp"]):
        return False, None

    return True, credentials


def is_valid_google_url(url: str) -> bool:
    VALID_SCHEME = "https"              # pylint: disable=C0103
    VALID_DOMAIN = "docs.google.com"    # pylint: disable=C0103
    try:
        result = urlparse(url)
        return (
            all([result.scheme, result.netloc])
            and result.scheme == VALID_SCHEME
            and result.netloc == VALID_DOMAIN
        )
    except ValueError:
        return False
