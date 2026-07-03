"""Authentication backend for Django ``User`` integration (v0.3.0).

Bridges a verified Google ``id_info`` payload to a Django ``User`` so that
``request.user`` is populated after the OAuth2 callback — **without any
django-gauth models or migrations**. The project's own ``User`` table
(``AUTH_USER_MODEL``) is used directly.

Register the backend alongside Django's default::

    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "django_gauth.backends.GoogleAuthBackend",
    ]
"""

from typing import Any, Optional

from django.contrib.auth import get_user_model  # pylint: disable=E0401
from django.contrib.auth.backends import BaseBackend  # pylint: disable=E0401

from django_gauth.utilities import get_or_create_user_from_id_info

__all__ = ["GoogleAuthBackend"]


class GoogleAuthBackend(BaseBackend):
    """Authenticate a Django ``User`` from a verified Google ``id_info``.

    The backend is intentionally passive for password logins: ``authenticate``
    returns ``None`` unless it is called with an ``id_info`` keyword, so it never
    interferes with Django's ``ModelBackend`` (username/password) or any other
    backend in the chain.
    """

    def authenticate(  # type: ignore[override]
        self,
        request: Any,
        id_info: Optional[dict] = None,
        **kwargs: Any,
    ) -> Optional[Any]:
        """Return a ``User`` for a verified ``id_info``, else ``None``.

        Args:
            request: The current request (unused, part of the backend contract).
            id_info: Verified Google ID-token claims. When ``None`` the backend
                opts out so other backends can handle the call.

        Returns:
            The authenticated ``User``, or ``None`` when authentication is
            refused (no ``id_info``, sign-in policy rejects it, or the user is
            inactive).
        """
        # Only act when explicitly handed a verified id_info payload.
        if id_info is None:
            return None

        user = get_or_create_user_from_id_info(id_info)
        if user is None:
            return None

        # Reject deactivated accounts (mirrors ModelBackend.user_can_authenticate).
        if not getattr(user, "is_active", True):
            return None

        return user

    def get_user(self, user_id: Any) -> Optional[Any]:
        """Reload a ``User`` by primary key on each request.

        Django persists the backend path in the session and calls this to
        rehydrate ``request.user`` on every subsequent request. Respects
        ``AUTH_USER_MODEL`` via ``get_user_model``.
        """
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
