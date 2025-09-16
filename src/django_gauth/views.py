"""
Auth Api's
~@ankit.kumar05
"""

from django.conf import settings                # pylint: disable=E0401
from django.shortcuts import redirect, render   # pylint: disable=E0401
from django.urls import reverse                 # pylint: disable=E0401
from google.auth.transport import requests      # pylint: disable=E0401
from google.oauth2 import id_token              # pylint: disable=E0401
from google_auth_oauthlib.flow import Flow      # pylint: disable=E0401

from django_gauth.utilities import check_gauth_authentication, credentials_to_dict

def index(request):  # type: ignore
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
    return render(request, "django_gauth/index.html", {"context_data": context})


def login(request):  # type: ignore
    """Login Api
    - Initiates the oauth2 Flow
    """
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

    request.session[settings.STATE_KEY_NAME] = state
    if (
        "final_redirect" not in request.session
        or not request.session[settings.FINAL_REDIRECT_KEY_NAME]
    ):
        request.session[settings.FINAL_REDIRECT_KEY_NAME] = (
            settings.GOOGLE_AUTH_FINAL_REDIRECT_URL
            or request.build_absolute_uri(reverse("django_gauth:index"))
        )  # directs where to land after login is successful.

    return redirect(authorization_url)


def callback(request):  # type: ignore
    """Google Oauth2 Callback
    - Google IDP response control transfer
    """
    # pull the state from the session
    session_state = request.session.get(settings.STATE_KEY_NAME)
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
        id_token=credentials._id_token,     # pylint: disable=W0212
        request=requests.Request(),
        audience=settings.GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=5,
    )
    # session setting
    request.session["id_info"] = id_info
    request.session[settings.CREDENTIALS_SESSION_KEY_NAME] = credentials_to_dict(credentials)
    # redirecting to the final redirect (i.e., logged in page)
    redirect_response = redirect(request.session[settings.FINAL_REDIRECT_KEY_NAME])

    return redirect_response
