"""
Auth Api's
~@ankit.kumar05
"""

import urllib.parse
from copy import deepcopy
from typing import Optional

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

import django_gauth.defaults as defaults
from django_gauth.utilities import check_gauth_authentication, credentials_to_dict

if not (hasattr(settings, "SCOPE") and settings.SCOPE):
    raise Exception(
        "[MissingGoogleScope] | missing required settings variable:`SCOPE`."
    )
else:
    SCOPE = settings.SCOPE

if not (hasattr(settings, "GOOGLE_CLIENT_ID") and settings.GOOGLE_CLIENT_ID):
    raise Exception(
        "[MissingGoogleClientCredentials] | missing required settings variable:`GOOGLE_CLIENT_ID`"
    )

if not (hasattr(settings, "GOOGLE_CLIENT_SECRET") and settings.GOOGLE_CLIENT_SECRET):
    raise Exception(
        "[MissingGoogleClientCredentials] | missing required settings variable:`GOOGLE_CLIENT_SECRET`"
    )

if (
    hasattr(settings, "GOOGLE_AUTH_FINAL_REDIRECT_URL")
    and settings.GOOGLE_AUTH_FINAL_REDIRECT_URL
):
    GOOGLE_AUTH_FINAL_REDIRECT_URL = settings.GOOGLE_AUTH_FINAL_REDIRECT_URL
else:
    GOOGLE_AUTH_FINAL_REDIRECT_URL = defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL

if (
    hasattr(settings, "CREDENTIALS_SESSION_KEY_NAME")
    and settings.CREDENTIALS_SESSION_KEY_NAME
):
    CREDENTIALS_SESSION_KEY_NAME = settings.CREDENTIALS_SESSION_KEY_NAME
else:
    CREDENTIALS_SESSION_KEY_NAME = defaults.CREDENTIALS_SESSION_KEY_NAME

if hasattr(settings, "STATE_KEY_NAME") and settings.STATE_KEY_NAME:
    STATE_KEY_NAME = settings.STATE_KEY_NAME
else:
    STATE_KEY_NAME = defaults.STATE_KEY_NAME

if hasattr(settings, "FINAL_REDIRECT_KEY_NAME") and settings.FINAL_REDIRECT_KEY_NAME:
    FINAL_REDIRECT_KEY_NAME = settings.STATE_KEY_NAME
else:
    FINAL_REDIRECT_KEY_NAME = defaults.FINAL_REDIRECT_KEY_NAME


def get_origin_url(request: HttpRequest) -> tuple[Optional[str], bool]:  # type: ignore
    """check origin url"""

    origin_url = request.GET.get("origin_url")
    # origin_url = request.headers.get('X-ORIGIN-URL')
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
    """Login Api
    - Initiates the oauth2 Flow
    """
    # Check for the authenticity of origin url
    origin_url, is_valid_origin = get_origin_url(
        request
    )  # Fetch from Header:X-ORIGIN-URL in future

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        # if you need additional scopes, add them here
        ,
        scopes=settings.SCOPE,
    )

    # flow.redirect_uri = get_redirect_uri(request) # use this when
    flow.redirect_uri = request.build_absolute_uri(reverse("django_gauth:callback"))

    authorization_url, state = flow.authorization_url(
        access_type="offline", prompt="select_account", include_granted_scopes="true"
    )

    request.session[STATE_KEY_NAME] = state
    if origin_url and is_valid_origin:
        request.session[FINAL_REDIRECT_KEY_NAME] = origin_url
    else:
        if (
            FINAL_REDIRECT_KEY_NAME not in request.session
            or not request.session[FINAL_REDIRECT_KEY_NAME]
        ):
            # directs where to land after login is successful.
            request.session[FINAL_REDIRECT_KEY_NAME] = (
                GOOGLE_AUTH_FINAL_REDIRECT_URL
                or request.build_absolute_uri(reverse("django_gauth:index"))
            )  # directs where to land after login is successful.
    # print("final redirect : ", GOOGLE_AUTH_FINAL_REDIRECT_URL or request.build_absolute_uri(reverse("django_gauth:index")))
    return redirect(authorization_url)


def callback(request: HttpRequest):  # type: ignore
    """Google Oauth2 Callback
    - Google IDP response control transfer
    """
    # pull the state from the session
    session_state = request.session.get(STATE_KEY_NAME)
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
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
            "https://www.googleapis.com/auth/drive",
        ],
        state=session_state,
    )

    flow.redirect_uri = redirect_uri
    # fetch token
    flow.fetch_token(authorization_response=authorization_response)
    # get credentials
    credentials = flow.credentials
    # verify token, while also retrieving information about the user
    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=requests.Request(),
        audience=settings.GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=5,
    )
    # session setting
    request.session["id_info"] = id_info
    request.session[settings.CREDENTIALS_SESSION_KEY_NAME] = credentials_to_dict(
        credentials
    )
    # redirecting to the final redirect (i.e., logged in page)
    redirect_response = redirect(request.session[FINAL_REDIRECT_KEY_NAME])

    return redirect_response


import copy


def debug_information(request: HttpRequest):  # type: ignore
    """
    Debug Information
    """
    session_data: dict = copy.deepcopy(dict(request.session))
    # sanitizing `id_info`
    if "id_info" in session_data:
        session_data["id_info"].pop("iss", None)
        session_data["id_info"].pop("azp", None)
        session_data["id_info"].pop("aud", None)
        session_data["id_info"].pop("sub", None)
    # sanitizing `credentials`
    if "credentials" in session_data:
        value = session_data.pop("credentials")
        session_data["debug"]["credentials_info"] = dict()
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
        # client id match info
        if "client_id" in value:
            session_data["debug"]["credentials_info"]["client_id_matches"] = (
                value["client_id"] == settings.GOOGLE_CLIENT_ID
            )
        # client secret match info
        if "client_secret" in value:
            session_data["debug"]["credentials_info"]["client_secret_matches"] = (
                value["client_secret"] == settings.GOOGLE_CLIENT_SECRET
            )
        # add scopes info
        if "scopes" in value:
            session_data["debug"]["credentials_info"]["scopes"] = value["scopes"]
    # sanitizing `oauth_state`
    if "oauth_state" in session_data:
        session_data.pop("oauth_state")
    return JsonResponse({"session": session_data})
