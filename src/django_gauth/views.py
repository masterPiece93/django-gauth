"""
Auth Api's
~@ankit.kumar05
"""

import urllib.parse
from copy import deepcopy
from typing import Optional

from django.conf import settings  # pylint: disable=import-error
from django.http import (  # pylint: disable=import-error
    HttpRequest,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import redirect, render  # pylint: disable=import-error
from django.urls import reverse  # pylint: disable=import-error
from google.auth.transport import requests  # pylint: disable=import-error
from google.oauth2 import id_token  # pylint: disable=import-error
from google_auth_oauthlib.flow import Flow  # pylint: disable=import-error

from django_gauth import defaults
from django_gauth.utilities import (
    RedirectionScheme,
    check_gauth_authentication,
    credentials_to_dict,
    get_credentials,
    revoke_google_token,
)


def get_origin_url(
    request: HttpRequest,
    retrieve_from: str = "query",
    retrieve_key: str = "origin_url",
) -> tuple[Optional[str], bool]:  # type: ignore
    """Retrieves and validates the origin URL.

    Args:
        request: The HTTP request object.
        retrieve_from: The source to retrieve the origin URL from.
            Must be either ``"query"`` or ``"header"``.
        retrieve_key: The key to look up in the chosen source.

    Returns:
        A tuple of (origin_url | None, is_valid_same_origin).
    """
    if retrieve_from == "query":
        origin_url = request.GET.get(retrieve_key)
    elif retrieve_from == "header":
        origin_url = request.headers.get(retrieve_key)
    else:
        raise ValueError(
            "ArgumentError | fn:get_origin_url | "
            "retrieve_from must be either 'query' or 'header'"
        )

    current_url = request.build_absolute_uri()

    if hasattr(settings, "DEBUG") and settings.DEBUG:
        request.session["debug"] = {
            "origin_url": {"raw_url": origin_url, "is_valid": False}
        }
    if not origin_url:
        return None, False

    parsed_origin_url = urllib.parse.urlparse(urllib.parse.unquote(origin_url))
    parsed_current_url = urllib.parse.urlparse(current_url)

    if hasattr(settings, "DEBUG") and settings.DEBUG:
        request.session["debug"]["origin_url"]["parsed_url"] = urllib.parse.unquote(
            origin_url
        )
        request.session["debug"]["origin_url"][
            "parsed_current_url.scheme"
        ] = parsed_current_url.scheme
        request.session["debug"]["origin_url"][
            "parsed_origin_url.scheme"
        ] = parsed_origin_url.scheme
        request.session["debug"]["origin_url"][
            "parsed_current_url.netloc"
        ] = parsed_current_url.netloc
        request.session["debug"]["origin_url"][
            "parsed_origin_url.netloc"
        ] = parsed_origin_url.netloc
        request.session["debug"]["origin_url"]["is_valid"] = (
            parsed_current_url.scheme == parsed_origin_url.scheme
            and parsed_current_url.netloc == parsed_origin_url.netloc
        )

    return urllib.parse.unquote(origin_url), (
        parsed_current_url.scheme == parsed_origin_url.scheme
        and parsed_current_url.netloc == parsed_origin_url.netloc
    )


# API
def index(request: HttpRequest):  # type: ignore
    is_authenticated, _ = check_gauth_authentication(request.session)
    id_info = request.session.get("id_info", {})

    id_info.pop("iss", None)
    id_info.pop("azp", None)
    id_info.pop("aud", None)
    id_info.pop("sub", None)

    context: dict = {
        "title": "",
        "login_href": reverse("django_gauth:login"),
        "user_info": id_info,
        "is_authenticated": is_authenticated,
    }

    if hasattr(settings, "DJANGO_GAUTH_UI_CONFIG"):
        ui_config = settings.DJANGO_GAUTH_UI_CONFIG
        if ui_config and "index" in ui_config:
            context["index"] = deepcopy(ui_config["index"])

    default_values = {
        "default_index_navbar_background": "#4b286d",
        "default_index_navbar_text_color": "white",
        "default_index_navbar_logo_background": "inherit",
    }
    context.update(default_values)

    return render(request, "django_gauth/index.html", {"context_data": context})


def login(request: HttpRequest):  # type: ignore
    """Login Api — Initiates the OAuth2 Flow.

    The ``scheme`` query parameter controls how the final redirect URL is
    resolved:

    - ``PRESERVE_ORIGIN_QP`` — reads ``origin_url`` from query params.
    - ``PRESERVE_ORIGIN_HP`` — reads ``X-ORIGIN-URL`` from request header.
    - ``LANDING_PAGE`` / ``DEFAULT`` — uses ``GOOGLE_AUTH_FINAL_REDIRECT_URL``
      or the package index.

    The ``response`` query parameter controls how the authorization URL is
    delivered to the caller:

    - ``redirect`` (default) — returns a 302 redirect to Google.
    - ``json`` — returns a ``JsonResponse`` with ``{"redirect_to": ...}``.
    """
    # Determine the redirection scheme from the ?scheme= query parameter.
    scheme_raw = request.GET.get("scheme", RedirectionScheme.DEFAULT.value)
    scheme_raw = scheme_raw.upper()

    # Determine the response type from the ?response= query parameter.
    response_type = request.GET.get("response", "redirect").lower()
    if response_type not in ("redirect", "json"):
        return HttpResponseBadRequest(
            f"Invalid response type '{response_type}'. "
            f"Valid options: ['redirect', 'json']"
        )

    # Resolve origin URL based on the selected scheme.
    origin_url: Optional[str] = None
    is_valid_origin: bool = False

    if scheme_raw == RedirectionScheme.PRESERVE_ORIGIN_HP.value:
        origin_url, is_valid_origin = get_origin_url(
            request, retrieve_from="header", retrieve_key="X-ORIGIN-URL"
        )
    elif scheme_raw == RedirectionScheme.PRESERVE_ORIGIN_QP.value:
        origin_url, is_valid_origin = get_origin_url(
            request, retrieve_from="query", retrieve_key="origin_url"
        )
    elif scheme_raw in (
        RedirectionScheme.LANDING_PAGE.value,
        RedirectionScheme.DEFAULT.name,
    ):
        origin_url = (
            settings.GOOGLE_AUTH_FINAL_REDIRECT_URL
            or request.build_absolute_uri(reverse("django_gauth:index"))
        )
        is_valid_origin = True
    else:
        return HttpResponseBadRequest(
            f"Invalid redirection scheme '{scheme_raw}'. "
            f"Valid options: {[m.name for m in RedirectionScheme]}"
        )

    # Auth Flow Setup
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=settings.SCOPE,
    )

    flow.redirect_uri = request.build_absolute_uri(reverse("django_gauth:callback"))

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt=settings.GOOGLE_LOGIN_PROMPT,
        include_granted_scopes="true",
    )

    # state initialization
    request.session[settings.STATE_KEY_NAME] = state

    # final redirect initialization
    if origin_url and is_valid_origin:
        request.session[settings.FINAL_REDIRECT_KEY_NAME] = origin_url
    else:
        if (
            settings.FINAL_REDIRECT_KEY_NAME not in request.session
            or not request.session[settings.FINAL_REDIRECT_KEY_NAME]
        ):
            request.session[settings.FINAL_REDIRECT_KEY_NAME] = (
                settings.GOOGLE_AUTH_FINAL_REDIRECT_URL
                or request.build_absolute_uri(reverse("django_gauth:index"))
            )

    # Conditional response based on ?response= parameter
    if response_type == "json":
        return JsonResponse({"redirect_to": authorization_url})
    return redirect(authorization_url)


def callback(request: HttpRequest):  # type: ignore
    """Google Oauth2 Callback
    - Google IDP response control transfer
    """
    # pull the state from the session
    session_state = request.session.get(settings.STATE_KEY_NAME)

    # ISSUE-5: handle provider-reported errors before assuming success. When the
    # user clicks "Deny" (or consent fails) Google redirects back with
    # ?error=access_denied and no code, so attempting a token exchange would
    # crash. Route to a graceful landing page instead.
    if request.GET.get("error"):
        fallback = request.session.get(settings.FINAL_REDIRECT_KEY_NAME)
        return redirect(fallback or reverse("django_gauth:index"))

    # ISSUE-4: explicitly verify the returned state matches the one we stored at
    # login. Defends against CSRF, expired sessions, and replayed callback links
    # by surfacing a clear error instead of a raw oauthlib stack trace.
    request_state = request.GET.get("state")
    if not session_state or not request_state or request_state != session_state:
        return HttpResponseBadRequest(
            "Invalid or missing OAuth state. Please restart the sign-in process."
        )

    redirect_uri = request.build_absolute_uri(reverse("django_gauth:callback"))
    authorization_response = request.build_absolute_uri()
    # Flow Creation
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=settings.SCOPE,
        state=session_state,
    )

    flow.redirect_uri = redirect_uri
    # fetch token
    flow.fetch_token(authorization_response=authorization_response)
    # get credentials
    credentials = flow.credentials
    # verify token, while also retrieving information about the user
    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=requests.Request(),
        audience=settings.GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=5,
    )
    # session setting
    request.session["id_info"] = id_info
    request.session[settings.CREDENTIALS_SESSION_KEY_NAME] = credentials_to_dict(
        credentials
    )
    # oauth_state is a single-use CSRF nonce — remove it now that auth is
    # complete so it doesn't linger in the authenticated session.
    request.session.pop(settings.STATE_KEY_NAME, None)

    # redirecting to the final redirect (i.e., logged in page)
    redirect_response = redirect(request.session[settings.FINAL_REDIRECT_KEY_NAME])

    return redirect_response


def logout(request: HttpRequest):  # type: ignore
    """Logout Api — clears the session and (optionally) revokes the Google token.

    Mirrors ``login()``'s ``?response=`` convention so it plugs cleanly into an
    SPA backend:

    - ``redirect`` *(default)* — `302` to ``GOOGLE_AUTH_LOGOUT_REDIRECT_URL``
      (or the package index).
    - ``json`` — `200` with ``{"status": "logged_out"}``.

    Upstream token revocation is best-effort and controlled by the
    ``GOOGLE_TOKEN_REVOKE_ON_LOGOUT`` setting (default ``True``). A revocation
    failure never blocks logout — the local session is always cleared.
    """
    response_type = request.GET.get("response", "redirect").lower()
    if response_type not in ("redirect", "json"):
        return HttpResponseBadRequest(
            f"Invalid response type '{response_type}'. "
            f"Valid options: ['redirect', 'json']"
        )

    # Best-effort upstream token revocation before the session is cleared.
    revoke_enabled = getattr(
        settings,
        "GOOGLE_TOKEN_REVOKE_ON_LOGOUT",
        defaults.GOOGLE_TOKEN_REVOKE_ON_LOGOUT,
    )
    credentials_key = settings.CREDENTIALS_SESSION_KEY_NAME or "credentials"
    if revoke_enabled and credentials_key in request.session:
        stored = request.session[credentials_key]
        # Prefer the refresh_token — revoking it also invalidates access tokens.
        token = stored.get("refresh_token") or stored.get("token")
        if token:
            revoke_google_token(token)

    # Clear the entire session (rotates the session key).
    request.session.flush()

    if response_type == "json":
        return JsonResponse({"status": "logged_out"})

    logout_redirect = getattr(settings, "GOOGLE_AUTH_LOGOUT_REDIRECT_URL", None)
    return redirect(logout_redirect or reverse("django_gauth:index"))


def session_status(request: HttpRequest):  # type: ignore
    """Session probe for SPA frontends.

    Returns the current authentication state as JSON, transparently refreshing
    the Google access token (and cached ``id_info``) when it has expired but a
    ``refresh_token`` is available. This is what lets sessions survive past the
    ~1 hour ID-token lifetime.

    Response shape:
        ``{"authenticated": bool, "user": {...} | null}``

    The ``user`` payload is the sanitized ``id_info`` (opaque ``iss``/``azp``/
    ``aud``/``sub`` claims are stripped), matching the landing page and debug
    endpoint.
    """
    credentials = get_credentials(request)
    if credentials is None:
        return JsonResponse({"authenticated": False, "user": None})

    user_info = deepcopy(request.session.get("id_info", {}))
    for claim in ("iss", "azp", "aud", "sub"):
        user_info.pop(claim, None)
    return JsonResponse({"authenticated": True, "user": user_info})


def debug_information(request: HttpRequest):  # type: ignore
    """
    Debug Information
    """
    session_data: dict = deepcopy(dict(request.session))
    # sanitizing `id_info`
    if "id_info" in session_data:
        session_data["id_info"].pop("iss", None)
        session_data["id_info"].pop("azp", None)
        session_data["id_info"].pop("aud", None)
        session_data["id_info"].pop("sub", None)
    # sanitizing `credentials`
    if "credentials" in session_data:
        value = session_data.pop("credentials")
        session_data["debug"]["credentials_info"] = {}
        # add token info
        if "token" in value and value["token"]:
            session_data["debug"]["credentials_info"]["token"] = "Exists"
        else:
            session_data["debug"]["credentials_info"]["token"] = "Not-Exists"
        # add refresh token info
        if "refresh_token" in value and value["refresh_token"]:
            session_data["debug"]["credentials_info"]["refresh_token"] = "Exists"
        else:
            session_data["debug"]["credentials_info"]["refresh_token"] = "Not-Exists"
        # add token_uri info
        if "token_uri" in value:
            session_data["debug"]["credentials_info"]["token_uri"] = value["token_uri"]
        # add scopes info
        if "scopes" in value:
            session_data["debug"]["credentials_info"]["scopes"] = value["scopes"]
    # sanitizing `oauth_state`
    # (already removed from session on successful auth, guarded here for safety)
    if "oauth_state" in session_data:
        session_data.pop("oauth_state")
    return JsonResponse({"session": session_data})
