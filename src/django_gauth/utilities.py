import enum
import time
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlencode, urlparse

from django.conf import Settings, settings  # pylint: disable=E0401
from django.contrib.auth import get_user_model  # pylint: disable=E0401
from django.utils.module_loading import import_string  # pylint: disable=E0401
from google.auth.transport import requests as google_requests  # pylint: disable=E0401
from google.oauth2 import id_token  # pylint: disable=E0401
from google.oauth2.credentials import Credentials  # pylint: disable=E0401

from django_gauth import defaults

__all__ = [
    "credentials_to_dict",
    "has_epoch_time_passed",
    "check_gauth_authentication",
    "is_valid_google_url",
    "RedirectionScheme",
    "revoke_google_token",
    "get_credentials",
    "get_session_expiry",
    "SESSION_LOGIN_AT_KEY",
    "SESSION_LAST_ACTIVE_KEY",
    "get_or_create_user_from_id_info",
]

# Internal session bookkeeping keys used by the session-policy layer.
# ``SESSION_LOGIN_AT_KEY`` is stamped once at ``callback`` time and is the anchor
# for the absolute-age cap — it is never overwritten on refresh.
# ``SESSION_LAST_ACTIVE_KEY`` tracks the last successful credential access and
# drives the idle timeout (only written when an idle timeout is configured).
SESSION_LOGIN_AT_KEY = "gauth_login_at"
SESSION_LAST_ACTIVE_KEY = "gauth_last_active"


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


def _within_session_policy(session: Any) -> bool:
    """Return whether the session is still within the configured policy bounds.

    Two independent, optional caps are enforced:

    - **Absolute age** (``GOOGLE_SESSION_MAX_AGE``) — measured from the login
      timestamp stamped at ``callback`` time (never moved on refresh).
    - **Idle timeout** (``GOOGLE_SESSION_IDLE_TIMEOUT``) — measured from the last
      successful credential access.

    A missing timestamp (e.g. a legacy session created before the policy was
    enabled) is treated as *satisfied* so existing users are not abruptly locked
    out. When neither cap is configured this always returns ``True``.
    """
    now = time.time()

    max_age = getattr(
        settings, "GOOGLE_SESSION_MAX_AGE", defaults.GOOGLE_SESSION_MAX_AGE
    )
    if max_age is not None:
        login_at = session.get(SESSION_LOGIN_AT_KEY)
        if login_at is not None and (now - login_at) > max_age:
            return False

    idle_timeout = getattr(
        settings, "GOOGLE_SESSION_IDLE_TIMEOUT", defaults.GOOGLE_SESSION_IDLE_TIMEOUT
    )
    if idle_timeout is not None:
        last_active = session.get(SESSION_LAST_ACTIVE_KEY)
        if last_active is not None and (now - last_active) > idle_timeout:
            return False

    return True


def _touch_last_active(session: Any) -> None:
    """Stamp the session's last-active time — only when an idle timeout applies.

    Skipping the write when no idle timeout is configured avoids a session save
    on every authenticated request, keeping behaviour identical to pre-policy
    releases when the feature is unused.
    """
    idle_timeout = getattr(
        settings, "GOOGLE_SESSION_IDLE_TIMEOUT", defaults.GOOGLE_SESSION_IDLE_TIMEOUT
    )
    if idle_timeout is None:
        return
    session[SESSION_LAST_ACTIVE_KEY] = time.time()
    if hasattr(session, "modified"):
        session.modified = True


def get_credentials(request: Any) -> Optional[Credentials]:
    """Return valid Google credentials for the request, refreshing if needed.

    This is the session-lifecycle accessor. It enforces the configurable session
    policy (:data:`GOOGLE_SESSION_AUTO_REFRESH`, :data:`GOOGLE_SESSION_MAX_AGE`,
    :data:`GOOGLE_SESSION_IDLE_TIMEOUT`) and, when policy allows, transparently
    refreshes an expired access token — re-verifying the fresh ``id_token`` and
    writing the refreshed credentials and ``id_info`` back to the session.

    Args:
        request: The Django request whose ``session`` holds the credentials.

    Returns:
        A valid ``Credentials`` object, or ``None`` when the user is not
        authenticated, the session policy has expired the session, or no refresh
        is possible.
    """
    session = request.session
    credentials_session_key = settings.CREDENTIALS_SESSION_KEY_NAME or "credentials"

    # No stored credentials → definitely unauthenticated.
    if credentials_session_key not in session:
        return None

    # Policy gate: absolute-age / idle-timeout caps expire the session even when
    # the underlying Google token is still technically valid.
    if not _within_session_policy(session):
        return None

    # Fast path: an unexpired session already has usable credentials.
    authenticated, credentials = check_gauth_authentication(session)
    if authenticated:
        _touch_last_active(session)
        return credentials

    # Slow path: transparent refresh — only when auto-refresh is enabled.
    auto_refresh = getattr(
        settings, "GOOGLE_SESSION_AUTO_REFRESH", defaults.GOOGLE_SESSION_AUTO_REFRESH
    )
    if not auto_refresh:
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
    _touch_last_active(session)
    if hasattr(session, "modified"):
        session.modified = True
    return credentials


def get_session_expiry(session: Any) -> Dict[str, Any]:
    """Compute the effective session-expiry deadline and its governing policy.

    Three independent deadlines may apply to an authenticated session; the
    *earliest* one wins because it is the first constraint the session will hit:

    - ``"token"`` — the Google ID-token expiry (``id_info.exp``).
    - ``"max_age"`` — the absolute-age cap
      (``login_at + GOOGLE_SESSION_MAX_AGE``).
    - ``"idle"`` — the idle timeout
      (``last_active + GOOGLE_SESSION_IDLE_TIMEOUT``).

    This is a pure read — it never mutates the session — so it is safe to call
    from status/display surfaces (e.g. the landing page) without disturbing the
    idle clock.

    Args:
        session: The Django session (or any mapping) to inspect.

    Returns:
        A dict ``{"expires_at": float | None, "policy": str | None,
        "expired": bool}``. ``expires_at`` and ``policy`` are ``None`` when no
        deadline is known (e.g. an unauthenticated session).
    """
    now = time.time()
    deadlines = []  # list of (deadline_epoch, policy_name)

    id_info = session.get("id_info") or {}
    token_exp = id_info.get("exp")
    if token_exp is not None:
        deadlines.append((float(token_exp), "token"))

    max_age = getattr(
        settings, "GOOGLE_SESSION_MAX_AGE", defaults.GOOGLE_SESSION_MAX_AGE
    )
    login_at = session.get(SESSION_LOGIN_AT_KEY)
    if max_age is not None and login_at is not None:
        deadlines.append((float(login_at) + float(max_age), "max_age"))

    idle_timeout = getattr(
        settings, "GOOGLE_SESSION_IDLE_TIMEOUT", defaults.GOOGLE_SESSION_IDLE_TIMEOUT
    )
    last_active = session.get(SESSION_LAST_ACTIVE_KEY)
    if idle_timeout is not None and last_active is not None:
        deadlines.append((float(last_active) + float(idle_timeout), "idle"))

    if not deadlines:
        return {"expires_at": None, "policy": None, "expired": False}

    expires_at, policy = min(deadlines, key=lambda item: item[0])
    return {
        "expires_at": expires_at,
        "policy": policy,
        "expired": now >= expires_at,
    }


def _resolve_user_setting(name: str) -> Any:
    """Read a ``GOOGLE_USER_*`` setting, falling back to the package default."""
    return getattr(settings, name, getattr(defaults, name))


def _unique_username(user_model: Any, email: str) -> str:
    """Derive a unique ``USERNAME_FIELD`` value from an email's local-part.

    Used only when auto-creating a ``User`` whose username field differs from
    its email field (e.g. the stock ``auth.User``). Collisions are resolved with
    an incrementing numeric suffix, respecting the field's ``max_length``.
    """
    username_field = user_model.USERNAME_FIELD
    # pylint: disable=protected-access
    max_length = user_model._meta.get_field(username_field).max_length or 150
    base = (email.split("@", 1)[0] or "user")[:max_length]
    candidate = base
    suffix = 1
    while user_model.objects.filter(
        **{f"{username_field}__iexact": candidate}
    ).exists():
        tail = str(suffix)
        candidate = f"{base[: max_length - len(tail)]}{tail}"
        suffix += 1
    return candidate


def _build_new_user(user_model: Any, email: str) -> Any:
    """Instantiate (but do not save) a new ``User`` with the minimum fields.

    Respects ``AUTH_USER_MODEL`` conventions (``USERNAME_FIELD`` / ``EMAIL_FIELD``)
    and marks the password unusable — OAuth users authenticate via Google, never
    a local password.
    """
    username_field = user_model.USERNAME_FIELD
    email_field = getattr(user_model, "EMAIL_FIELD", "email")

    new_user_kwargs: Dict[str, Any] = {}
    if email_field:
        new_user_kwargs[email_field] = email
    if username_field == email_field:
        new_user_kwargs[username_field] = email
    else:
        new_user_kwargs[username_field] = _unique_username(user_model, email)

    user = user_model(**new_user_kwargs)
    user.set_unusable_password()
    return user


def _default_user_mapper(id_info: Dict[str, Any], user: Any) -> None:
    """Populate common name fields from Google claims when they are empty."""
    if hasattr(user, "first_name") and not getattr(user, "first_name", ""):
        user.first_name = id_info.get("given_name", "")
    if hasattr(user, "last_name") and not getattr(user, "last_name", ""):
        user.last_name = id_info.get("family_name", "")


def _apply_user_mapper(id_info: Dict[str, Any], user: Any, created: bool) -> None:
    """Dispatch to the configured ``GOOGLE_USER_MAPPER`` or the default mapper."""
    mapper_path = _resolve_user_setting("GOOGLE_USER_MAPPER")
    if mapper_path:
        import_string(mapper_path)(id_info, user, created)
    else:
        _default_user_mapper(id_info, user)


def get_or_create_user_from_id_info(id_info: Dict[str, Any]) -> Optional[Any]:
    """Resolve a Django ``User`` from a verified Google ``id_info`` payload.

    This is the model-free bridge behind
    :class:`django_gauth.backends.GoogleAuthBackend`. It never creates any
    django-gauth tables — it get-or-creates the project's own ``User``
    (respecting ``AUTH_USER_MODEL``) keyed on a configurable, case-insensitive
    field.

    Behaviour is governed by:
        - ``GOOGLE_USER_REQUIRE_VERIFIED_EMAIL`` — reject unverified emails.
        - ``GOOGLE_USER_LOOKUP_FIELD`` — the field matched (case-insensitive).
        - ``GOOGLE_USER_AUTO_CREATE`` — create on first login, or login-only.
        - ``GOOGLE_USER_MAPPER`` — dotted path to a field-population hook.

    Args:
        id_info: The verified ID-token claims from Google.

    Returns:
        The matched or newly-created ``User``, or ``None`` when sign-in must be
        refused (unverified email, missing lookup value, or no match while
        auto-create is disabled).
    """
    if not id_info:
        return None

    # 1. Verified-email guard — the primary anti-account-takeover control.
    require_verified = _resolve_user_setting("GOOGLE_USER_REQUIRE_VERIFIED_EMAIL")
    if require_verified and not id_info.get("email_verified"):
        return None

    email = id_info.get("email")
    if not email:
        return None

    user_model = get_user_model()
    lookup_field = _resolve_user_setting("GOOGLE_USER_LOOKUP_FIELD") or "email"
    lookup_value = email if lookup_field == "email" else id_info.get(lookup_field)
    if not lookup_value:
        return None

    # 2. Case-insensitive lookup against the project's own User table.
    user = user_model.objects.filter(
        **{f"{lookup_field}__iexact": lookup_value}
    ).first()
    created = False

    # 3. Get-or-create (creation is opt-in via GOOGLE_USER_AUTO_CREATE).
    if user is None:
        if not _resolve_user_setting("GOOGLE_USER_AUTO_CREATE"):
            return None
        user = _build_new_user(user_model, email)
        created = True

    # 4. Populate fields via the configured (or default) mapper.
    _apply_user_mapper(id_info, user, created)

    # 5. Persist (mapper changes apply to existing users too).
    user.save()
    return user
