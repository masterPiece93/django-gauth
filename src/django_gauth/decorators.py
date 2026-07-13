"""
View-protection helpers for django-gauth.

Provides a decorator (:func:`gauth_required`) and a class-based-view mixin
(:class:`GauthRequiredMixin`) that gate access on the visitor being
authenticated. Both are *dual-mode* and mirror the ``?response=`` convention
used by the login/logout endpoints:

- When :ref:`Django User integration <GOOGLE_USER_INTEGRATION>` is enabled,
  authentication is read from ``request.user.is_authenticated`` (so the same
  guard also honours admin/password logins).
- Otherwise it falls back to the session-lifecycle accessor
  (:func:`~django_gauth.utilities.get_credentials`), keeping the
  SPA/session-only story intact with no User model required.

In **both** modes the session-policy layer (``GOOGLE_SESSION_MAX_AGE``,
``GOOGLE_SESSION_IDLE_TIMEOUT``) is enforced so that expired sessions are
rejected even when Django's auth middleware still considers the user valid.

On failure the guard either issues a ``302`` redirect to the login endpoint
(``response="redirect"``, the default) or returns a ``401`` JSON body
(``response="json"``) suited to SPA/XHR callers.

.. note::
   **Scope: Django native views only.** These helpers target Django's native
   view contract (``django.http.HttpRequest``, ``request.session``, and
   ``request.user`` as populated by ``AuthenticationMiddleware``). They are
   **not** compatible with `Django REST Framework
   <https://www.django-rest-framework.org/>`_ views (``APIView``, ``ViewSet``,
   ``@api_view``), where authentication flows through DRF ``authentication_classes``
   / ``permission_classes`` and failures are raised as DRF exceptions rather than
   returned as redirects. DRF-native adapters are planned; until then, guard DRF
   endpoints with DRF's own authentication and permission classes.
"""

import functools
from typing import Callable, Optional

from django.conf import settings  # pylint: disable=E0401
from django.http import JsonResponse  # pylint: disable=E0401
from django.shortcuts import redirect  # pylint: disable=E0401
from django.urls import reverse  # pylint: disable=E0401

from django_gauth import defaults
from django_gauth.utilities import (
    _touch_last_active,
    _within_session_policy,
    get_credentials,
)

__all__ = ["gauth_required", "GauthRequiredMixin"]

_VALID_RESPONSES = ("redirect", "json")


def _request_is_authenticated(request) -> bool:  # type: ignore
    """Dual-mode authentication probe shared by the decorator and the mixin.

    Reads ``request.user`` when Django User integration is enabled, otherwise
    falls back to the session-lifecycle accessor :func:`get_credentials` which
    enforces session policy (``GOOGLE_SESSION_MAX_AGE``,
    ``GOOGLE_SESSION_IDLE_TIMEOUT``) and handles transparent token refresh.

    In *both* modes the session-policy layer is consulted so that absolute-age
    and idle-timeout caps are respected even when Django's auth middleware still
    considers the session valid.
    """
    integration_enabled = getattr(
        settings,
        "GOOGLE_USER_INTEGRATION",
        defaults.GOOGLE_USER_INTEGRATION,
    )
    if integration_enabled:
        user = getattr(request, "user", None)
        if not (user is not None and user.is_authenticated):
            return False
        # Enforce session-policy caps for Google-originated logins.
        # _within_session_policy gracefully returns True when the gauth
        # timestamps are absent (e.g. admin/password login) — so non-Google
        # sessions pass through unaffected.
        if not _within_session_policy(request.session):
            return False
        _touch_last_active(request.session)
        return True
    # Non-integration path: get_credentials enforces policy, touches idle,
    # and handles auto-refresh in one shot.
    return get_credentials(request) is not None


def _unauthenticated_response(response_type: str, login_url: Optional[str]):  # type: ignore
    """Build the failure response for an unauthenticated request."""
    if response_type == "json":
        return JsonResponse(
            {"detail": "Authentication required.", "authenticated": False},
            status=401,
        )
    return redirect(login_url or reverse("django_gauth:login"))


def gauth_required(
    view_func: Optional[Callable] = None,
    *,
    response: str = "redirect",
    login_url: Optional[str] = None,
) -> Callable:
    """Protect a function-based view, requiring an authenticated visitor.

    Usable bare or parameterised::

        @gauth_required
        def dashboard(request): ...

        @gauth_required(response="json")
        def api_me(request): ...

        @gauth_required(login_url="/accounts/login/")
        def billing(request): ...

    Args:
        view_func: The wrapped view (supplied automatically when used bare).
        response: ``"redirect"`` (302 to the login endpoint, default) or
            ``"json"`` (401 JSON body) on failure.
        login_url: Optional override for the redirect target. Defaults to
            ``reverse("django_gauth:login")``.

    Returns:
        The wrapped view, or a decorator when called with keyword arguments.

    Raises:
        ValueError: If ``response`` is not ``"redirect"`` or ``"json"``.
    """
    if response not in _VALID_RESPONSES:
        raise ValueError(
            f"Invalid response type '{response}'. "
            f"Valid options: {list(_VALID_RESPONSES)}"
        )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrapped(request, *args, **kwargs):  # type: ignore
            if _request_is_authenticated(request):
                return func(request, *args, **kwargs)
            return _unauthenticated_response(response, login_url)

        return _wrapped

    # Support both ``@gauth_required`` and ``@gauth_required(...)``.
    if view_func is not None:
        return decorator(view_func)
    return decorator


class GauthRequiredMixin:  # pylint: disable=R0903
    """Class-based-view mixin requiring an authenticated visitor.

    Mirrors :func:`gauth_required`. Place it *before* the base view so
    ``super().dispatch`` resolves correctly, and configure via class
    attributes::

        class Dashboard(GauthRequiredMixin, TemplateView):
            template_name = "dashboard.html"

        class MeView(GauthRequiredMixin, View):
            gauth_response = "json"

    Attributes:
        gauth_response: ``"redirect"`` (default) or ``"json"``.
        gauth_login_url: Optional redirect-target override.
    """

    gauth_response: str = "redirect"
    gauth_login_url: Optional[str] = None

    def dispatch(self, request, *args, **kwargs):  # type: ignore
        if self.gauth_response not in _VALID_RESPONSES:
            raise ValueError(
                f"Invalid gauth_response '{self.gauth_response}'. "
                f"Valid options: {list(_VALID_RESPONSES)}"
            )
        if not _request_is_authenticated(request):
            return _unauthenticated_response(self.gauth_response, self.gauth_login_url)
        return super().dispatch(request, *args, **kwargs)  # type: ignore
