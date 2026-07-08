from typing import Final, Optional

GOOGLE_AUTH_FINAL_REDIRECT_URL: Final[Optional[str]] = (
    None  # auto selects django_gauth > index.html
)
CREDENTIALS_SESSION_KEY_NAME: Final[str] = "credentials"
STATE_KEY_NAME: Final[str] = "oauth_state"
FINAL_REDIRECT_KEY_NAME: Final[str] = "final_redirect"
GOOGLE_LOGIN_PROMPT: Final[str] = "select_account consent"
# Session lifecycle (v0.4.0)
# When True, ``logout`` best-effort revokes the upstream Google token before
# flushing the local session.
GOOGLE_TOKEN_REVOKE_ON_LOGOUT: Final[bool] = True
# Where ``logout`` redirects to when called with ``?response=redirect``.
# ``None`` falls back to the package index page.
GOOGLE_AUTH_LOGOUT_REDIRECT_URL: Final[Optional[str]] = None

# Session policy (v0.4.0)
# Master switch for transparent access-token refresh in ``get_credentials``.
# When False, an expired session simply ends and the user must re-authenticate
# instead of being silently refreshed.
GOOGLE_SESSION_AUTO_REFRESH: Final[bool] = True
# Absolute session cap in seconds. When set, ``get_credentials`` refuses to
# extend a session older than ``login_time + GOOGLE_SESSION_MAX_AGE`` — even when
# a valid refresh token is available. ``None`` disables the absolute cap.
GOOGLE_SESSION_MAX_AGE: Final[Optional[int]] = None
# Idle timeout in seconds. When set, ``get_credentials`` ends a session that has
# been inactive for longer than this window. ``None`` disables the idle timeout.
GOOGLE_SESSION_IDLE_TIMEOUT: Final[Optional[int]] = None

# Django User integration (v0.3.0)
# Master switch: when True, the OAuth2 callback logs a Django ``User`` in via
# ``django.contrib.auth.login`` so ``request.user`` is populated. Requires
# ``django_gauth.backends.GoogleAuthBackend`` in ``AUTHENTICATION_BACKENDS``.
GOOGLE_USER_INTEGRATION: Final[bool] = False
# When True, a matching ``User`` is created on first login (get-or-create).
# When False, only pre-existing users can sign in (invite-only).
GOOGLE_USER_AUTO_CREATE: Final[bool] = True
# The ``User`` field matched against the Google account, case-insensitively.
GOOGLE_USER_LOOKUP_FIELD: Final[str] = "email"
# When True, reject sign-in unless Google reports the email as verified.
GOOGLE_USER_REQUIRE_VERIFIED_EMAIL: Final[bool] = True
# Dotted path to a ``(id_info, user, created) -> None`` callable that populates
# the ``User`` from Google claims. ``None`` uses the built-in default mapper.
GOOGLE_USER_MAPPER: Final[Optional[str]] = None
