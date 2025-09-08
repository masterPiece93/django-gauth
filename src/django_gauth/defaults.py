from typing import Final, Optional

GOOGLE_AUTH_FINAL_REDIRECT_URL: Final[Optional[str]] = None # auto selects django_gauth > index.html
CREDENTIALS_SESSION_KEY_NAME: Final[str] = "credentials"
STATE_KEY_NAME: Final[str] = "oauth_state"
FINAL_REDIRECT_KEY_NAME: Final[str] = "final_redirect"
