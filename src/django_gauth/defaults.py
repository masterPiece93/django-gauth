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
