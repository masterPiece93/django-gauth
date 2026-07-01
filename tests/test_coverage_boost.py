"""
Extended unit tests to boost coverage across:
- admin.py
- defaults.py
- _checks.py
- apps.py (set_defaults)
- utilities.py
- views.py (index, login, get_origin_url, debug_information, callback)
"""

import time
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import TestCase, RequestFactory, override_settings
from django.test.client import Client
from django.urls import reverse

from django_gauth import defaults
from django_gauth._checks import (
    ErrorCodes,
    check_project_middlewares,
    check_project_settings,
    formulate_check_id,
)
from django_gauth.utilities import (
    credentials_to_dict,
    has_epoch_time_passed,
    check_gauth_authentication,
    is_valid_google_url,
)


# ============================================================
# defaults.py — Import coverage
# ============================================================
class DefaultsTest(TestCase):
    """Cover defaults.py constants"""

    def test_defaults_values(self):
        self.assertIsNone(defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL)
        self.assertEqual(defaults.CREDENTIALS_SESSION_KEY_NAME, "credentials")
        self.assertEqual(defaults.STATE_KEY_NAME, "oauth_state")
        self.assertEqual(defaults.FINAL_REDIRECT_KEY_NAME, "final_redirect")
        self.assertEqual(defaults.GOOGLE_LOGIN_PROMPT, "select_account consent")


# ============================================================
# _checks.py — check_project_settings & check_project_middlewares
# ============================================================
class CheckProjectSettingsTest(TestCase):
    """Cover _checks.check_project_settings branches"""

    def test_no_errors_when_all_settings_present(self):
        """No errors when required settings exist"""
        errors = check_project_settings(app_configs=None)
        self.assertEqual(errors, [])

    @override_settings()
    def test_missing_google_client_id(self):
        """Error when GOOGLE_CLIENT_ID is absent"""
        del settings.GOOGLE_CLIENT_ID
        errors = check_project_settings(app_configs=None)
        ids = [e.id for e in errors]
        self.assertIn(formulate_check_id(ErrorCodes.E003.name), ids)

    @override_settings()
    def test_missing_google_client_secret(self):
        """Error when GOOGLE_CLIENT_SECRET is absent"""
        del settings.GOOGLE_CLIENT_SECRET
        errors = check_project_settings(app_configs=None)
        ids = [e.id for e in errors]
        self.assertIn(formulate_check_id(ErrorCodes.E003.name), ids)

    @override_settings()
    def test_missing_secret_key(self):
        """Error when SECRET_KEY is absent"""
        del settings.SECRET_KEY
        errors = check_project_settings(app_configs=None)
        ids = [e.id for e in errors]
        self.assertIn(formulate_check_id(ErrorCodes.E001.name), ids)


class CheckProjectMiddlewaresTest(TestCase):
    """Cover _checks.check_project_middlewares"""

    def test_no_error_with_session_middleware(self):
        errors = check_project_middlewares(app_configs=None)
        self.assertEqual(errors, [])

    @override_settings(MIDDLEWARE=[])
    def test_error_when_session_middleware_missing(self):
        errors = check_project_middlewares(app_configs=None)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, formulate_check_id(ErrorCodes.E002.name))


class ErrorCodesTest(TestCase):
    """Cover ErrorCodes enum"""

    def test_error_codes_values(self):
        self.assertEqual(ErrorCodes.E001.value[0], "MISSING_REQUIRED_SETTINGS")
        self.assertEqual(ErrorCodes.E002.value[0], "MISSING_REQUIRED_MIDDLEWARE")
        self.assertEqual(
            ErrorCodes.E003.value[0], "MISSING_REQUIRED_GOOGLE_CREDENTIALS"
        )
        self.assertEqual(ErrorCodes.E004.value[0], "INVALID_GAUTH_SCOPE")

    def test_formulate_check_id(self):
        self.assertEqual(formulate_check_id("E001"), "django_gauth.E001")


# ============================================================
# apps.py — set_defaults
# ============================================================
class SetDefaultsTest(TestCase):
    """Cover apps.set_defaults branches"""

    def _call_set_defaults(self):
        from django_gauth.apps import set_defaults

        return set_defaults(app_configs=None)

    @override_settings()
    def test_scope_not_defined(self):
        """SCOPE not defined → warning + default"""
        if hasattr(settings, "SCOPE"):
            del settings.SCOPE
        errors = self._call_set_defaults()
        # Should have set SCOPE to []
        self.assertEqual(settings.SCOPE, [])
        ids = [e.id for e in errors if hasattr(e, "id") and e.id]
        self.assertIn(formulate_check_id(ErrorCodes.E004.name), ids)

    @override_settings(SCOPE=[])
    def test_scope_defined(self):
        """SCOPE defined → no warning for scope"""
        errors = self._call_set_defaults()
        scope_errors = [
            e
            for e in errors
            if hasattr(e, "id") and e.id and ErrorCodes.E004.name in e.id
        ]
        self.assertEqual(scope_errors, [])

    @override_settings()
    def test_google_auth_final_redirect_url_not_defined(self):
        """Sets default when GOOGLE_AUTH_FINAL_REDIRECT_URL is absent"""
        if hasattr(settings, "GOOGLE_AUTH_FINAL_REDIRECT_URL"):
            del settings.GOOGLE_AUTH_FINAL_REDIRECT_URL
        self._call_set_defaults()
        self.assertEqual(
            settings.GOOGLE_AUTH_FINAL_REDIRECT_URL,
            defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL,
        )

    @override_settings(GOOGLE_AUTH_FINAL_REDIRECT_URL="")
    def test_google_auth_final_redirect_url_empty(self):
        """No error when GOOGLE_AUTH_FINAL_REDIRECT_URL is an empty string.

        The enhancement only flags values that are explicitly set to a
        non-empty string that is not a valid URL.  An empty string is treated
        as 'not configured' and does not produce an Info entry.
        """
        errors = self._call_set_defaults()
        redirect_infos = [
            e
            for e in errors
            if hasattr(e, "msg") and "GOOGLE_AUTH_FINAL_REDIRECT_URL" in str(e.msg)
        ]
        self.assertEqual(redirect_infos, [])

    @override_settings(GOOGLE_AUTH_FINAL_REDIRECT_URL="not-a-valid-url")
    def test_google_auth_final_redirect_url_invalid_value(self):
        """Info error when GOOGLE_AUTH_FINAL_REDIRECT_URL is set to a
        non-empty string that is not a valid URL."""
        errors = self._call_set_defaults()
        self.assertTrue(len(errors) >= 1)

    @override_settings(GOOGLE_AUTH_FINAL_REDIRECT_URL="http://example.com")
    def test_google_auth_final_redirect_url_valid(self):
        """No info when GOOGLE_AUTH_FINAL_REDIRECT_URL is truthy"""
        errors = self._call_set_defaults()
        redirect_infos = [
            e
            for e in errors
            if hasattr(e, "msg") and "GOOGLE_AUTH_FINAL_REDIRECT_URL" in str(e.msg)
        ]
        self.assertEqual(redirect_infos, [])

    @override_settings()
    def test_credentials_session_key_name_not_defined(self):
        """Sets default when CREDENTIALS_SESSION_KEY_NAME is absent"""
        if hasattr(settings, "CREDENTIALS_SESSION_KEY_NAME"):
            del settings.CREDENTIALS_SESSION_KEY_NAME
        self._call_set_defaults()
        self.assertEqual(
            settings.CREDENTIALS_SESSION_KEY_NAME,
            defaults.CREDENTIALS_SESSION_KEY_NAME,
        )

    @override_settings(CREDENTIALS_SESSION_KEY_NAME="")
    def test_credentials_session_key_name_empty(self):
        """Info when CREDENTIALS_SESSION_KEY_NAME is falsy"""
        errors = self._call_set_defaults()
        self.assertTrue(len(errors) >= 1)

    @override_settings()
    def test_state_key_name_not_defined(self):
        """Sets default when STATE_KEY_NAME is absent"""
        if hasattr(settings, "STATE_KEY_NAME"):
            del settings.STATE_KEY_NAME
        self._call_set_defaults()
        self.assertEqual(settings.STATE_KEY_NAME, defaults.STATE_KEY_NAME)

    @override_settings(STATE_KEY_NAME="")
    def test_state_key_name_empty(self):
        """Info when STATE_KEY_NAME is falsy"""
        errors = self._call_set_defaults()
        self.assertTrue(len(errors) >= 1)

    @override_settings()
    def test_final_redirect_key_name_not_defined(self):
        """Sets default when FINAL_REDIRECT_KEY_NAME is absent"""
        if hasattr(settings, "FINAL_REDIRECT_KEY_NAME"):
            del settings.FINAL_REDIRECT_KEY_NAME
        self._call_set_defaults()
        self.assertEqual(
            settings.FINAL_REDIRECT_KEY_NAME, defaults.FINAL_REDIRECT_KEY_NAME
        )

    @override_settings(FINAL_REDIRECT_KEY_NAME="")
    def test_final_redirect_key_name_empty(self):
        """Info when FINAL_REDIRECT_KEY_NAME is falsy"""
        errors = self._call_set_defaults()
        self.assertTrue(len(errors) >= 1)

    @override_settings()
    def test_google_login_prompt_not_defined(self):
        """Sets default when GOOGLE_LOGIN_PROMPT is absent."""
        if hasattr(settings, "GOOGLE_LOGIN_PROMPT"):
            del settings.GOOGLE_LOGIN_PROMPT
        self._call_set_defaults()
        self.assertEqual(settings.GOOGLE_LOGIN_PROMPT, defaults.GOOGLE_LOGIN_PROMPT)

    @override_settings(GOOGLE_LOGIN_PROMPT="")
    def test_google_login_prompt_empty(self):
        """Info error when GOOGLE_LOGIN_PROMPT is set to an empty string."""
        errors = self._call_set_defaults()
        self.assertTrue(len(errors) >= 1)


# ============================================================
# apps.py — is_url helper
# ============================================================
class IsUrlTest(TestCase):
    """Cover apps.is_url including the ValueError exception path."""

    def _is_url(self, value):
        from django_gauth.apps import is_url

        return is_url(value)

    def test_valid_url_returns_true(self):
        self.assertTrue(self._is_url("https://example.com/path"))

    def test_no_scheme_returns_false(self):
        self.assertFalse(self._is_url("example.com"))

    def test_empty_string_returns_false(self):
        self.assertFalse(self._is_url(""))

    @patch("django_gauth.apps.urlparse")
    def test_urlparse_value_error_returns_false(self, mock_urlparse):
        """except ValueError branch — urlparse raises → is_url returns False."""
        mock_urlparse.side_effect = ValueError("bad url")
        self.assertFalse(self._is_url("anything"))


# ============================================================
# urls.py — conditional debug endpoint
# ============================================================
class UrlsConfigTest(TestCase):
    """Cover urls.py conditional debug endpoint registration (line 18)."""

    def test_debug_url_registered_when_debug_is_true(self):
        """urlpatterns.append(debug path) is reached when DEBUG=True.

        Django's TestRunner forces DEBUG=False before tests run, so the
        module-level ``if settings.DEBUG:`` block never fires during a normal
        import.  We reload the module inside an override_settings(DEBUG=True)
        context to cover that branch, then reload again afterward to restore
        the module to its test-runner state.
        """
        import importlib

        import django_gauth.urls as gauth_urls

        with override_settings(DEBUG=True):
            importlib.reload(gauth_urls)
            url_names = [p.name for p in gauth_urls.urlpatterns]
            self.assertIn("debug", url_names)

        # Restore the module to its correct test-runner state (DEBUG=False)
        importlib.reload(gauth_urls)


# ============================================================
# utilities.py
# ============================================================
class CredentialsToDictTest(TestCase):
    """Cover utilities.credentials_to_dict"""

    def test_credentials_to_dict(self):
        mock_cred = MagicMock()
        mock_cred.token = "access_token_123"
        mock_cred.refresh_token = "refresh_token_456"
        mock_cred.token_uri = "https://oauth2.googleapis.com/token"
        mock_cred.client_id = "client_id_789"
        mock_cred.client_secret = "secret_abc"
        mock_cred.scopes = ["openid", "email"]

        result = credentials_to_dict(mock_cred)
        self.assertEqual(result["token"], "access_token_123")
        self.assertEqual(result["refresh_token"], "refresh_token_456")
        self.assertEqual(result["token_uri"], "https://oauth2.googleapis.com/token")
        self.assertEqual(result["scopes"], ["openid", "email"])
        # client_id/client_secret must never be persisted in the session (ISSUE-2)
        self.assertNotIn("client_id", result)
        self.assertNotIn("client_secret", result)


class HasEpochTimePassedTest(TestCase):
    """Cover utilities.has_epoch_time_passed"""

    def test_past_time_returns_true(self):
        past = time.time() - 1000
        self.assertTrue(has_epoch_time_passed(past))

    def test_future_time_returns_false(self):
        future = time.time() + 10000
        self.assertFalse(has_epoch_time_passed(future))

    def test_current_time_returns_true(self):
        now = time.time()
        self.assertTrue(has_epoch_time_passed(now))


class CheckGauthAuthenticationTest(TestCase):
    """Cover utilities.check_gauth_authentication"""

    def test_no_credentials_in_session(self):
        session = {}
        authenticated, cred = check_gauth_authentication(session)
        self.assertFalse(authenticated)
        self.assertIsNone(cred)

    @patch("django_gauth.utilities.Credentials")
    def test_credentials_invalid(self, mock_credentials_class):
        mock_cred_instance = MagicMock()
        mock_cred_instance.valid = False
        mock_credentials_class.return_value = mock_cred_instance

        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "tok",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": [],
            }
        }
        authenticated, cred = check_gauth_authentication(session)
        self.assertFalse(authenticated)
        self.assertIsNone(cred)

    @patch("django_gauth.utilities.Credentials")
    def test_credentials_valid_no_id_info(self, mock_credentials_class):
        mock_cred_instance = MagicMock()
        mock_cred_instance.valid = True
        mock_credentials_class.return_value = mock_cred_instance

        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "tok",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": [],
            }
        }
        authenticated, cred = check_gauth_authentication(session)
        self.assertTrue(authenticated)
        self.assertEqual(cred, mock_cred_instance)

    @patch("django_gauth.utilities.Credentials")
    def test_credentials_valid_expired_id_info(self, mock_credentials_class):
        mock_cred_instance = MagicMock()
        mock_cred_instance.valid = True
        mock_credentials_class.return_value = mock_cred_instance

        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "tok",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": [],
            },
            "id_info": {"exp": time.time() - 1000},  # expired
        }
        authenticated, cred = check_gauth_authentication(session)
        self.assertFalse(authenticated)
        self.assertIsNone(cred)

    @patch("django_gauth.utilities.Credentials")
    def test_credentials_valid_unexpired_id_info(self, mock_credentials_class):
        mock_cred_instance = MagicMock()
        mock_cred_instance.valid = True
        mock_credentials_class.return_value = mock_cred_instance

        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "tok",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": [],
            },
            "id_info": {"exp": time.time() + 10000},  # not expired
        }
        authenticated, cred = check_gauth_authentication(session)
        self.assertTrue(authenticated)
        self.assertEqual(cred, mock_cred_instance)


class CheckGauthClientSecretReinjectionTest(TestCase):
    """ISSUE-2 regression: client_id/secret come from settings, not the session"""

    @override_settings(
        GOOGLE_CLIENT_ID="cfg-client-id", GOOGLE_CLIENT_SECRET="cfg-client-secret"
    )
    @patch("django_gauth.utilities.Credentials")
    def test_client_id_secret_injected_from_settings(self, mock_credentials_class):
        mock_credentials_class.return_value.valid = True
        # the persisted blob deliberately carries NO client_id/client_secret
        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "tok",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["openid"],
            }
        }
        check_gauth_authentication(session)
        # rebuilt Credentials must receive the values from settings
        _, kwargs = mock_credentials_class.call_args
        self.assertEqual(kwargs["client_id"], "cfg-client-id")
        self.assertEqual(kwargs["client_secret"], "cfg-client-secret")
        self.assertNotIn(
            "client_secret", session[settings.CREDENTIALS_SESSION_KEY_NAME]
        )


class IsValidGoogleUrlTest(TestCase):
    """Cover utilities.is_valid_google_url"""

    def test_valid_google_docs_url(self):
        url = "https://docs.google.com/document/d/abc123/edit"
        self.assertTrue(is_valid_google_url(url))

    def test_http_scheme_invalid(self):
        url = "http://docs.google.com/document/d/abc123/edit"
        self.assertFalse(is_valid_google_url(url))

    def test_wrong_domain(self):
        url = "https://drive.google.com/file/d/abc123/view"
        self.assertFalse(is_valid_google_url(url))

    def test_empty_string(self):
        self.assertFalse(is_valid_google_url(""))

    def test_malformed_url(self):
        self.assertFalse(is_valid_google_url("not a url"))

    def test_no_scheme(self):
        self.assertFalse(is_valid_google_url("docs.google.com/document"))

    @patch("django_gauth.utilities.urlparse")
    def test_urlparse_value_error_returns_false(self, mock_urlparse):
        """except ValueError branch — urlparse raises → is_valid_google_url returns False."""
        mock_urlparse.side_effect = ValueError("bad url")
        self.assertFalse(is_valid_google_url("anything"))


# ============================================================
# admin.py — SessionAdmin
# ============================================================
class SessionAdminTest(TestCase):
    """Cover admin.py SessionAdmin registration and _session_data"""

    def test_session_admin_registered(self):
        from django.contrib.admin.sites import site

        self.assertIn(Session, site._registry)

    def test_session_admin_session_data_method(self):
        from django_gauth.admin import SessionAdmin

        admin_instance = SessionAdmin(Session, None)
        # Create a mock session object
        mock_session = MagicMock()
        mock_session.get_decoded.return_value = {"key": "value", "another": "data"}

        result = admin_instance._session_data(mock_session)
        self.assertIn("key", result)
        self.assertIn("value", result)

    def test_session_admin_list_display(self):
        from django_gauth.admin import SessionAdmin

        self.assertIn("session_key", SessionAdmin.list_display)
        self.assertIn("_session_data", SessionAdmin.list_display)
        self.assertIn("expire_date", SessionAdmin.list_display)

    def test_session_admin_readonly_fields(self):
        from django_gauth.admin import SessionAdmin

        self.assertIn("_session_data", SessionAdmin.readonly_fields)

    def test_session_admin_exclude(self):
        from django_gauth.admin import SessionAdmin

        self.assertIn("session_data", SessionAdmin.exclude)


# ============================================================
# views.py — get_origin_url
# ============================================================
@override_settings(DEBUG=True)
class GetOriginUrlTest(TestCase):
    """Cover views.get_origin_url"""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_request(self, origin_url=None):
        url = "/gauth/"
        if origin_url:
            url += f"?origin_url={origin_url}"
        request = self.factory.get(url)
        request.session = {}
        return request

    def test_no_origin_url(self):
        from django_gauth.views import get_origin_url

        request = self._make_request()
        result, is_valid = get_origin_url(request)
        self.assertIsNone(result)
        self.assertFalse(is_valid)

    def test_valid_same_origin_url(self):
        from django_gauth.views import get_origin_url

        request = self._make_request(origin_url="http%3A//testserver/some-page/")
        result, is_valid = get_origin_url(request)
        self.assertEqual(result, "http://testserver/some-page/")
        self.assertTrue(is_valid)

    def test_different_origin_url(self):
        from django_gauth.views import get_origin_url

        request = self._make_request(origin_url="https%3A//other.com/page/")
        result, is_valid = get_origin_url(request)
        self.assertEqual(result, "https://other.com/page/")
        self.assertFalse(is_valid)

    def test_debug_session_populated(self):
        from django_gauth.views import get_origin_url

        request = self._make_request(origin_url="http%3A//testserver/page/")
        get_origin_url(request)
        self.assertIn("debug", request.session)
        self.assertIn("origin_url", request.session["debug"])


@override_settings(DEBUG=False)
class GetOriginUrlNonDebugTest(TestCase):
    """Cover get_origin_url with DEBUG=False"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_no_debug_data_in_session(self):
        from django_gauth.views import get_origin_url

        request = self.factory.get("/gauth/?origin_url=http%3A//testserver/x/")
        request.session = {}
        get_origin_url(request)
        self.assertNotIn("debug", request.session)


# ============================================================
# views.py — index view
# ============================================================
class IndexViewExtendedTest(TestCase):
    """Cover views.index with various settings"""

    def setUp(self):
        self.client = Client()

    def test_index_unauthenticated(self):
        response = self.client.get(reverse("django_gauth:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("context_data", response.context)
        self.assertFalse(response.context["context_data"]["is_authenticated"])

    @override_settings(
        DJANGO_GAUTH_UI_CONFIG={
            "index": {
                "navbar": {
                    "logo": "https://example.com/logo.png",
                    "profile_picture_absence": "https://example.com/placeholder.png",
                }
            }
        }
    )
    def test_index_with_ui_config(self):
        response = self.client.get(reverse("django_gauth:index"))
        self.assertEqual(response.status_code, 200)
        context = response.context["context_data"]
        self.assertIn("index", context)
        self.assertEqual(
            context["index"]["navbar"]["logo"], "https://example.com/logo.png"
        )

    def test_index_default_navbar_values(self):
        response = self.client.get(reverse("django_gauth:index"))
        context = response.context["context_data"]
        self.assertEqual(context["default_index_navbar_background"], "#4b286d")
        self.assertEqual(context["default_index_navbar_text_color"], "white")
        self.assertEqual(context["default_index_navbar_logo_background"], "inherit")


# ============================================================
# views.py — login view
# ============================================================
class LoginViewExtendedTest(TestCase):
    """Cover views.login with origin_url scenarios"""

    def setUp(self):
        self.client = Client()

    def test_login_redirect_to_google(self):
        response = self.client.get(reverse("django_gauth:login"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response.url)

    def test_login_with_valid_origin_url(self):
        login_url = reverse("django_gauth:login")
        origin = "http://testserver/my-app/"
        response = self.client.get(
            f"{login_url}?scheme=PRESERVE_ORIGIN_QP&origin_url={origin}"
        )
        self.assertEqual(response.status_code, 302)
        # Check final_redirect was set in session
        session = self.client.session
        self.assertEqual(session[settings.FINAL_REDIRECT_KEY_NAME], origin)

    def test_login_with_invalid_origin_url(self):
        login_url = reverse("django_gauth:login")
        origin = "https://evil.com/steal/"
        response = self.client.get(
            f"{login_url}?scheme=PRESERVE_ORIGIN_QP&origin_url={origin}"
        )
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        # Should not set evil origin; should use default
        self.assertNotEqual(session.get(settings.FINAL_REDIRECT_KEY_NAME), origin)

    def test_login_sets_state_in_session(self):
        self.client.get(reverse("django_gauth:login"))
        session = self.client.session
        self.assertIn(settings.STATE_KEY_NAME, session)

    def test_login_preserve_origin_hp_returns_json(self):
        """PRESERVE_ORIGIN_HP scheme with response=json: returns JsonResponse."""
        login_url = reverse("django_gauth:login")
        response = self.client.get(
            f"{login_url}?scheme=PRESERVE_ORIGIN_HP&response=json",
            HTTP_X_ORIGIN_URL="http://testserver/dashboard/",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        import json

        data = json.loads(response.content)
        self.assertIn("redirect_to", data)
        self.assertIn("accounts.google.com", data["redirect_to"])
        # final_redirect should be set to the origin header value
        session = self.client.session
        self.assertEqual(
            session[settings.FINAL_REDIRECT_KEY_NAME], "http://testserver/dashboard/"
        )

    def test_login_preserve_origin_hp_with_redirect_response(self):
        """PRESERVE_ORIGIN_HP scheme with response=redirect: returns 302."""
        login_url = reverse("django_gauth:login")
        response = self.client.get(
            f"{login_url}?scheme=PRESERVE_ORIGIN_HP&response=redirect",
            HTTP_X_ORIGIN_URL="http://testserver/dashboard/",
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response.url)

    def test_login_invalid_response_type_returns_400(self):
        """Invalid response query param should return 400."""
        login_url = reverse("django_gauth:login")
        response = self.client.get(f"{login_url}?response=xml")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid response type", response.content)

    def test_login_json_response_with_landing_page_scheme(self):
        """LANDING_PAGE scheme with response=json: returns JsonResponse."""
        login_url = reverse("django_gauth:login")
        response = self.client.get(f"{login_url}?scheme=LANDING_PAGE&response=json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        import json

        data = json.loads(response.content)
        self.assertIn("redirect_to", data)
        self.assertIn("accounts.google.com", data["redirect_to"])

    def test_login_invalid_scheme_returns_400(self):
        """Invalid scheme query param should return 400."""
        login_url = reverse("django_gauth:login")
        response = self.client.get(f"{login_url}?scheme=NONSENSE")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid redirection scheme", response.content)

    def test_login_landing_page_scheme_uses_configured_url(self):
        """LANDING_PAGE scheme uses GOOGLE_AUTH_FINAL_REDIRECT_URL."""
        login_url = reverse("django_gauth:login")
        response = self.client.get(f"{login_url}?scheme=LANDING_PAGE")
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        # With default settings (GOOGLE_AUTH_FINAL_REDIRECT_URL=None),
        # should fall back to the index page URL
        self.assertIn("/gauth/", session[settings.FINAL_REDIRECT_KEY_NAME])


# ============================================================
# views.py — get_origin_url retrieve_from variants
# ============================================================
@override_settings(DEBUG=True)
class GetOriginUrlHeaderTest(TestCase):
    """Cover get_origin_url with retrieve_from='header'."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_origin_from_header(self):
        from django_gauth.views import get_origin_url

        request = self.factory.get(
            "/gauth/login/", HTTP_X_ORIGIN_URL="http://testserver/page/"
        )
        request.session = {}
        result, is_valid = get_origin_url(
            request, retrieve_from="header", retrieve_key="X-ORIGIN-URL"
        )
        self.assertEqual(result, "http://testserver/page/")
        self.assertTrue(is_valid)

    def test_origin_from_header_missing(self):
        from django_gauth.views import get_origin_url

        request = self.factory.get("/gauth/login/")
        request.session = {}
        result, is_valid = get_origin_url(
            request, retrieve_from="header", retrieve_key="X-ORIGIN-URL"
        )
        self.assertIsNone(result)
        self.assertFalse(is_valid)

    def test_invalid_retrieve_from_raises(self):
        from django_gauth.views import get_origin_url

        request = self.factory.get("/gauth/login/")
        request.session = {}
        with self.assertRaises(ValueError):
            get_origin_url(request, retrieve_from="body", retrieve_key="origin_url")


# ============================================================
# views.py — debug_information (using RequestFactory to avoid URL resolution issues)
# ============================================================
@override_settings(DEBUG=True)
class DebugInformationViewTest(TestCase):
    """Cover views.debug_information"""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_request(self, session_data=None):
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import debug_information

        request = self.factory.get("/gauth/debug")
        session = SessionStore()
        if session_data:
            for key, value in session_data.items():
                session[key] = value
        session.create()
        request.session = session
        return debug_information(request)

    def test_debug_empty_session(self):
        response = self._make_request(session_data={"debug": {}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_debug_with_id_info(self):
        session_data = {
            "debug": {},
            "id_info": {
                "iss": "accounts.google.com",
                "azp": "xxxx",
                "aud": "yyyy",
                "sub": "1234",
                "email": "test@example.com",
                "name": "Test User",
            },
        }
        response = self._make_request(session_data=session_data)
        self.assertEqual(response.status_code, 200)
        import json

        data = json.loads(response.content)
        # iss, azp, aud, sub should be sanitized out
        self.assertNotIn("iss", data["session"].get("id_info", {}))
        self.assertNotIn("azp", data["session"].get("id_info", {}))
        self.assertNotIn("sub", data["session"].get("id_info", {}))
        # email should remain
        self.assertIn("email", data["session"]["id_info"])

    def test_debug_with_credentials(self):
        session_data = {
            "debug": {},
            "credentials": {
                "token": "access_tok",
                "refresh_token": "ref_tok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["openid"],
            },
        }
        response = self._make_request(session_data=session_data)
        self.assertEqual(response.status_code, 200)
        import json

        data = json.loads(response.content)
        cred_info = data["session"]["debug"]["credentials_info"]
        self.assertEqual(cred_info["token"], "Exists")
        self.assertEqual(cred_info["refresh_token"], "Exists")
        self.assertEqual(cred_info["scopes"], ["openid"])
        # client_id/client_secret are no longer persisted, so never reported (ISSUE-2)
        self.assertNotIn("client_id_matches", cred_info)
        self.assertNotIn("client_secret_matches", cred_info)

    def test_debug_with_credentials_no_token(self):
        session_data = {
            "debug": {},
            "credentials": {
                "token": "",
                "refresh_token": "",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": [],
            },
        }
        response = self._make_request(session_data=session_data)
        import json

        data = json.loads(response.content)
        cred_info = data["session"]["debug"]["credentials_info"]
        self.assertEqual(cred_info["token"], "Not-Exists")
        self.assertEqual(cred_info["refresh_token"], "Not-Exists")

    def test_debug_with_oauth_state(self):
        session_data = {
            "debug": {},
            "oauth_state": "random_state_string",
        }
        response = self._make_request(session_data=session_data)
        import json

        data = json.loads(response.content)
        # oauth_state should be stripped from response
        self.assertNotIn("oauth_state", data["session"])

    def test_debug_credentials_missing_keys(self):
        """Cover branches where token_uri/scopes keys are absent"""
        session_data = {
            "debug": {},
            "credentials": {
                "token": "tok",
                "refresh_token": None,
            },
        }
        response = self._make_request(session_data=session_data)
        import json

        data = json.loads(response.content)
        cred_info = data["session"]["debug"]["credentials_info"]
        self.assertEqual(cred_info["token"], "Exists")
        self.assertEqual(cred_info["refresh_token"], "Not-Exists")


# ============================================================
# views.py — callback view (mocked OAuth flow)
# ============================================================
class CallbackViewTest(TestCase):
    """Cover views.callback with mocked Google OAuth flow"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_success(self, mock_flow_class, mock_verify):
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        # Setup mock flow
        mock_flow_instance = MagicMock()
        mock_flow_class.return_value = mock_flow_instance

        mock_credentials = MagicMock()
        mock_credentials.token = "access_token"
        mock_credentials.refresh_token = "refresh_token"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = settings.GOOGLE_CLIENT_ID
        mock_credentials.client_secret = settings.GOOGLE_CLIENT_SECRET
        mock_credentials.scopes = ["openid"]
        mock_credentials.id_token = "fake_id_token"
        mock_flow_instance.credentials = mock_credentials

        # Setup mock id_token verification
        mock_verify.return_value = {
            "iss": "accounts.google.com",
            "email": "user@example.com",
            "name": "Test User",
            "exp": time.time() + 3600,
        }

        # Create request
        request = self.factory.get(
            "/gauth/login-callback?state=test_state&code=test_code"
        )
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "test_state"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/gauth/"
        session.create()
        request.session = session

        response = callback(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "http://testserver/gauth/")

        # Verify session was populated
        self.assertIn("id_info", request.session)
        self.assertIn(settings.CREDENTIALS_SESSION_KEY_NAME, request.session)
        # ISSUE-3 regression: callback must read the public ``id_token`` property,
        # not the private ``_id_token`` attribute.
        self.assertEqual(mock_verify.call_args.kwargs["id_token"], "fake_id_token")

    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_sets_credentials_in_session(self, mock_flow_class, mock_verify):
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        mock_flow_instance = MagicMock()
        mock_flow_class.return_value = mock_flow_instance

        mock_credentials = MagicMock()
        mock_credentials.token = "my_access_token"
        mock_credentials.refresh_token = "my_refresh_token"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = settings.GOOGLE_CLIENT_ID
        mock_credentials.client_secret = settings.GOOGLE_CLIENT_SECRET
        mock_credentials.scopes = ["openid", "email"]
        mock_credentials.id_token = "id_tok"
        mock_flow_instance.credentials = mock_credentials

        mock_verify.return_value = {
            "email": "user2@example.com",
            "exp": time.time() + 7200,
        }

        request = self.factory.get("/gauth/login-callback?state=s&code=c")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "s"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/"
        session.create()
        request.session = session

        callback(request)

        creds = request.session[settings.CREDENTIALS_SESSION_KEY_NAME]
        self.assertEqual(creds["token"], "my_access_token")
        self.assertEqual(creds["refresh_token"], "my_refresh_token")
        self.assertEqual(creds["scopes"], ["openid", "email"])
        # ISSUE-2: client secret must never be persisted in the session
        self.assertNotIn("client_secret", creds)
        self.assertNotIn("client_id", creds)
        # oauth_state must be removed on successful auth (single-use CSRF nonce)
        self.assertNotIn(settings.STATE_KEY_NAME, request.session)

    @override_settings(
        SCOPE=[
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
        ]
    )
    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_uses_settings_scope(self, mock_flow_class, mock_verify):
        """ISSUE-1 regression: callback must use settings.SCOPE, not a hardcoded list.

        Guards against the authorization request and token exchange diverging
        (which produces confusing "Scope has changed" errors).
        """
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        mock_flow_instance = MagicMock()
        mock_flow_class.return_value = mock_flow_instance
        mock_credentials = MagicMock()
        mock_credentials.scopes = settings.SCOPE
        mock_credentials.id_token = "id_tok"
        mock_flow_instance.credentials = mock_credentials
        mock_verify.return_value = {
            "email": "user@example.com",
            "exp": time.time() + 3600,
        }

        request = self.factory.get("/gauth/login-callback?state=s&code=c")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "s"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/"
        session.create()
        request.session = session

        callback(request)

        # The scopes passed to Flow must match settings.SCOPE exactly
        _, kwargs = mock_flow_class.call_args
        self.assertEqual(kwargs["scopes"], settings.SCOPE)
        # And must not contain the previously hardcoded drive scope
        self.assertNotIn("https://www.googleapis.com/auth/drive", kwargs["scopes"])

    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_state_mismatch_returns_400(self, mock_flow_class):
        """ISSUE-4: a returned state that differs from the session state is rejected."""
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        request = self.factory.get("/gauth/login-callback?state=evil&code=c")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "expected"
        session.create()
        request.session = session

        response = callback(request)
        self.assertEqual(response.status_code, 400)
        # the OAuth flow must never be exercised on a bad state
        mock_flow_class.assert_not_called()

    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_missing_request_state_returns_400(self, mock_flow_class):
        """ISSUE-4: a callback without a state query param is rejected."""
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        request = self.factory.get("/gauth/login-callback?code=c")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "expected"
        session.create()
        request.session = session

        response = callback(request)
        self.assertEqual(response.status_code, 400)
        mock_flow_class.assert_not_called()

    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_missing_session_state_returns_400(self, mock_flow_class):
        """ISSUE-4: a missing/expired session state is rejected."""
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        request = self.factory.get("/gauth/login-callback?state=s&code=c")
        session = SessionStore()
        session.create()
        request.session = session

        response = callback(request)
        self.assertEqual(response.status_code, 400)
        mock_flow_class.assert_not_called()

    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_access_denied_redirects_gracefully(self, mock_flow_class):
        """ISSUE-5: error=access_denied lands on the configured redirect, no crash."""
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        request = self.factory.get("/gauth/login-callback?error=access_denied&state=s")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "s"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/home/"
        session.create()
        request.session = session

        response = callback(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "http://testserver/home/")
        # the OAuth flow must not be touched when the user cancelled
        mock_flow_class.assert_not_called()

    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_error_without_redirect_falls_back_to_index(self, mock_flow_class):
        """ISSUE-5: with no stored redirect, errors land on the package index."""
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        request = self.factory.get("/gauth/login-callback?error=server_error")
        session = SessionStore()
        session.create()
        request.session = session

        response = callback(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/gauth", response.url)
        mock_flow_class.assert_not_called()

    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_clears_oauth_state_after_success(
        self, mock_flow_class, mock_verify
    ):
        """oauth_state is a single-use CSRF nonce; it must be removed from the
        session once authentication completes so it cannot linger post-auth."""
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        mock_flow_instance = MagicMock()
        mock_flow_class.return_value = mock_flow_instance
        mock_credentials = MagicMock()
        mock_credentials.token = "tok"
        mock_credentials.refresh_token = "rtok"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.scopes = ["openid"]
        mock_credentials.id_token = "id_tok"
        mock_flow_instance.credentials = mock_credentials
        mock_verify.return_value = {"email": "u@example.com", "exp": time.time() + 3600}

        request = self.factory.get("/gauth/login-callback?state=s&code=c")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "s"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/"
        session.create()
        request.session = session

        # state exists before the callback
        self.assertIn(settings.STATE_KEY_NAME, request.session)

        callback(request)

        # state must be gone after successful auth
        self.assertNotIn(settings.STATE_KEY_NAME, request.session)
        # credentials and id_info must still be present
        self.assertIn(settings.CREDENTIALS_SESSION_KEY_NAME, request.session)
        self.assertIn("id_info", request.session)
