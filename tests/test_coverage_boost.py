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
from django.http import HttpResponse
from django.test import TestCase, RequestFactory, override_settings
from django.test.client import Client
from django.urls import reverse

from django_gauth import defaults
from django_gauth._checks import (
    ErrorCodes,
    check_project_middlewares,
    check_project_settings,
    check_user_integration_requirements,
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
        # session lifecycle (v0.4.0)
        self.assertTrue(defaults.GOOGLE_TOKEN_REVOKE_ON_LOGOUT)
        self.assertIsNone(defaults.GOOGLE_AUTH_LOGOUT_REDIRECT_URL)
        # session policy (v0.4.0)
        self.assertTrue(defaults.GOOGLE_SESSION_AUTO_REFRESH)
        self.assertIsNone(defaults.GOOGLE_SESSION_MAX_AGE)
        self.assertIsNone(defaults.GOOGLE_SESSION_IDLE_TIMEOUT)

    def test_user_integration_defaults(self):
        # Django User integration (v0.3.0) — safe, opt-in defaults
        self.assertFalse(defaults.GOOGLE_USER_INTEGRATION)
        self.assertTrue(defaults.GOOGLE_USER_AUTO_CREATE)
        self.assertEqual(defaults.GOOGLE_USER_LOOKUP_FIELD, "email")
        self.assertTrue(defaults.GOOGLE_USER_REQUIRE_VERIFIED_EMAIL)
        self.assertIsNone(defaults.GOOGLE_USER_MAPPER)


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


class CheckUserIntegrationRequirementsTest(TestCase):
    """Cover _checks.check_user_integration_requirements (v0.3.0 Phase 3)."""

    def test_no_warnings_when_integration_disabled(self):
        # Default: GOOGLE_USER_INTEGRATION is off → inert, empty result.
        self.assertEqual(check_user_integration_requirements(app_configs=None), [])

    @override_settings(
        GOOGLE_USER_INTEGRATION=True,
        AUTHENTICATION_BACKENDS=[
            "django_gauth.backends.GoogleAuthBackend",
            "django.contrib.auth.backends.ModelBackend",
        ],
    )
    def test_no_warnings_when_fully_wired(self):
        # auth app + AuthenticationMiddleware come from the base test settings.
        self.assertEqual(check_user_integration_requirements(app_configs=None), [])

    @override_settings(GOOGLE_USER_INTEGRATION=True)
    def test_warns_when_backend_missing(self):
        # Default AUTHENTICATION_BACKENDS = [ModelBackend] → GoogleAuthBackend absent.
        errors = check_user_integration_requirements(app_configs=None)
        ids = [e.id for e in errors]
        self.assertIn(formulate_check_id(ErrorCodes.W003.name), ids)

    @override_settings(
        GOOGLE_USER_INTEGRATION=True,
        MIDDLEWARE=[],
        AUTHENTICATION_BACKENDS=[
            "django_gauth.backends.GoogleAuthBackend",
            "django.contrib.auth.backends.ModelBackend",
        ],
    )
    def test_warns_when_auth_middleware_missing(self):
        errors = check_user_integration_requirements(app_configs=None)
        ids = [e.id for e in errors]
        self.assertIn(formulate_check_id(ErrorCodes.W002.name), ids)

    @override_settings(
        GOOGLE_USER_INTEGRATION=True,
        AUTHENTICATION_BACKENDS=[
            "django_gauth.backends.GoogleAuthBackend",
            "django.contrib.auth.backends.ModelBackend",
        ],
    )
    def test_warns_when_auth_app_missing(self):
        # Direct-assign INSTALLED_APPS (no registry reload) so the membership
        # test sees auth absent; restored in finally + by override_settings exit.
        original = list(settings.INSTALLED_APPS)
        try:
            settings.INSTALLED_APPS = [
                app for app in original if app != "django.contrib.auth"
            ]
            errors = check_user_integration_requirements(app_configs=None)
            ids = [e.id for e in errors]
            self.assertIn(formulate_check_id(ErrorCodes.W001.name), ids)
        finally:
            settings.INSTALLED_APPS = original

    def test_warning_codes_defined(self):
        self.assertEqual(
            ErrorCodes.W001.value[0], "MISSING_AUTH_APP_FOR_USER_INTEGRATION"
        )
        self.assertEqual(
            ErrorCodes.W002.value[0], "MISSING_AUTH_MIDDLEWARE_FOR_USER_INTEGRATION"
        )
        self.assertEqual(
            ErrorCodes.W003.value[0], "MISSING_AUTH_BACKEND_FOR_USER_INTEGRATION"
        )


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
# apps.py — apply_setting_defaults (runs from AppConfig.ready)
# ============================================================
class ApplySettingDefaultsTest(TestCase):
    """Cover apps.apply_setting_defaults.

    This is the gunicorn/uwsgi/asgi-safe path: unlike the ``set_defaults``
    system check (which Django only runs for a few management commands), this
    runs from ``AppConfig.ready()`` for every server, so the defaults are always
    present at runtime.
    """

    def _apply(self):
        from django_gauth.apps import apply_setting_defaults

        return apply_setting_defaults()

    @override_settings()
    def test_fills_all_absent_settings(self):
        """Every optional setting that is absent gets its packaged default."""
        for name in (
            "SCOPE",
            "GOOGLE_AUTH_FINAL_REDIRECT_URL",
            "CREDENTIALS_SESSION_KEY_NAME",
            "STATE_KEY_NAME",
            "FINAL_REDIRECT_KEY_NAME",
            "GOOGLE_LOGIN_PROMPT",
        ):
            if hasattr(settings, name):
                delattr(settings, name)

        self._apply()

        self.assertEqual(settings.SCOPE, [])
        self.assertEqual(
            settings.GOOGLE_AUTH_FINAL_REDIRECT_URL,
            defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL,
        )
        self.assertEqual(
            settings.CREDENTIALS_SESSION_KEY_NAME,
            defaults.CREDENTIALS_SESSION_KEY_NAME,
        )
        self.assertEqual(settings.STATE_KEY_NAME, defaults.STATE_KEY_NAME)
        self.assertEqual(
            settings.FINAL_REDIRECT_KEY_NAME, defaults.FINAL_REDIRECT_KEY_NAME
        )
        self.assertEqual(settings.GOOGLE_LOGIN_PROMPT, defaults.GOOGLE_LOGIN_PROMPT)

    @override_settings(
        SCOPE=["openid"],
        STATE_KEY_NAME="custom_state",
        GOOGLE_LOGIN_PROMPT="consent",
    )
    def test_is_idempotent_and_preserves_user_values(self):
        """User-defined settings are never overwritten (idempotent fill)."""
        self._apply()
        self.assertEqual(settings.SCOPE, ["openid"])
        self.assertEqual(settings.STATE_KEY_NAME, "custom_state")
        self.assertEqual(settings.GOOGLE_LOGIN_PROMPT, "consent")

    def test_ready_applies_defaults_for_wsgi_servers(self):
        """Regression: AppConfig.ready() must apply defaults, since gunicorn/
        uwsgi/asgi never trigger the system-check framework."""
        from django.apps import apps as django_apps

        app_config = django_apps.get_app_config("django_gauth")
        # Remove a couple of settings a WSGI import would rely on...
        for name in ("STATE_KEY_NAME", "GOOGLE_LOGIN_PROMPT"):
            if hasattr(settings, name):
                delattr(settings, name)

        # ...then re-run ready() (what django.setup() does under gunicorn).
        app_config.ready()

        self.assertEqual(settings.STATE_KEY_NAME, defaults.STATE_KEY_NAME)
        self.assertEqual(settings.GOOGLE_LOGIN_PROMPT, defaults.GOOGLE_LOGIN_PROMPT)


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
        # No prior session → not a policy expiry, just anonymous.
        self.assertFalse(response.context["context_data"]["session_expired"])
        self.assertIsNone(
            response.context["context_data"]["session_expiry"]["expires_at"]
        )

    def test_index_exposes_login_and_logout_hrefs(self):
        """The landing page provides both an Authenticate and a Logout control."""
        response = self.client.get(reverse("django_gauth:index"))
        context = response.context["context_data"]
        self.assertEqual(context["login_href"], reverse("django_gauth:login"))
        self.assertEqual(context["logout_href"], reverse("django_gauth:logout"))
        # Both buttons are rendered (visibility is toggled client-side by JS).
        self.assertContains(response, 'id="AuthenticateButton"')
        self.assertContains(response, 'id="LogoutButton"')
        self.assertContains(response, reverse("django_gauth:logout"))

    @override_settings(GOOGLE_SESSION_MAX_AGE=300)
    def test_index_reflects_max_age_expiry(self):
        """A session past GOOGLE_SESSION_MAX_AGE shows as expired on the landing
        page (previously it wrongly appeared authenticated)."""
        from django_gauth.utilities import SESSION_LOGIN_AT_KEY

        session = self.client.session
        session[settings.CREDENTIALS_SESSION_KEY_NAME] = {
            "token": "tok",
            "refresh_token": "rtok",
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": ["openid"],
        }
        session["id_info"] = {"exp": time.time() + 3600, "email": "u@example.com"}
        # login was 10 minutes ago → beyond the 5-minute cap
        session[SESSION_LOGIN_AT_KEY] = time.time() - 600
        session.save()

        response = self.client.get(reverse("django_gauth:index"))
        context = response.context["context_data"]
        self.assertFalse(context["is_authenticated"])
        self.assertTrue(context["session_expired"])
        self.assertEqual(context["session_expiry"]["policy"], "max_age")
        self.assertEqual(
            context["session_expiry"]["policy_label"], "maximum session age"
        )
        # The re-authentication message is surfaced in the rendered page.
        self.assertContains(response, "session has expired")

    @override_settings(GOOGLE_SESSION_MAX_AGE=3600)
    @patch("django_gauth.views.get_credentials")
    def test_index_authenticated_exposes_effective_expiry(self, mock_get_creds):
        """When authenticated, the countdown target is the effective policy
        deadline (max-age here), not just the Google token exp."""
        from django_gauth.utilities import SESSION_LOGIN_AT_KEY

        mock_get_creds.return_value = object()  # authenticated

        session = self.client.session
        session["id_info"] = {"exp": time.time() + 7200, "email": "u@example.com"}
        login_at = time.time()
        session[SESSION_LOGIN_AT_KEY] = login_at
        session.save()

        response = self.client.get(reverse("django_gauth:index"))
        context = response.context["context_data"]
        self.assertTrue(context["is_authenticated"])
        self.assertFalse(context["session_expired"])
        # max-age deadline (login_at + 3600) is earlier than the token exp (7200)
        self.assertEqual(context["session_expiry"]["policy"], "max_age")
        self.assertAlmostEqual(
            context["session_expiry"]["expires_at"], login_at + 3600, delta=2
        )

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
        # session lifecycle: the login time is stamped as the absolute-age anchor
        from django_gauth.utilities import SESSION_LOGIN_AT_KEY

        self.assertIn(SESSION_LOGIN_AT_KEY, request.session)
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

    @override_settings(
        SCOPE=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
            "https://www.googleapis.com/auth/drive",
        ]
    )
    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_logs_warning_on_scope_reduction(
        self, mock_flow_class, mock_verify
    ):
        """When Google grants fewer scopes than requested, a warning is logged
        but the callback still succeeds (no crash)."""
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        mock_flow_instance = MagicMock()
        mock_flow_class.return_value = mock_flow_instance

        mock_credentials = MagicMock()
        mock_credentials.token = "tok"
        mock_credentials.refresh_token = "rtok"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        # Google drops the drive scope
        mock_credentials.scopes = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
        ]
        mock_credentials.id_token = "id_tok"
        mock_flow_instance.credentials = mock_credentials
        mock_verify.return_value = {"email": "u@example.com", "exp": time.time() + 3600}

        request = self.factory.get("/gauth/login-callback?state=s&code=c")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "s"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/"
        session.create()
        request.session = session

        with self.assertLogs("django_gauth.views", level="WARNING") as cm:
            response = callback(request)

        # Callback still succeeds with a redirect
        self.assertEqual(response.status_code, 302)
        # A warning was emitted about the dropped scope
        self.assertTrue(
            any("drive" in msg for msg in cm.output),
            f"Expected drive scope in warning log, got: {cm.output}",
        )

    @override_settings(GOOGLE_SESSION_IDLE_TIMEOUT=60)
    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_resets_idle_clock_on_relogin(
        self, mock_flow_class, mock_verify
    ):
        """Re-login must reset the idle clock so a stale gauth_last_active from a
        prior (expired) session does not immediately expire the fresh one."""
        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.utilities import (
            SESSION_LAST_ACTIVE_KEY,
            SESSION_LOGIN_AT_KEY,
        )
        from django_gauth.views import callback

        mock_flow_instance = MagicMock()
        mock_flow_class.return_value = mock_flow_instance
        mock_credentials = MagicMock()
        mock_credentials.token = "tok"
        mock_credentials.refresh_token = "rtok"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.scopes = settings.SCOPE
        mock_credentials.id_token = "id_tok"
        mock_flow_instance.credentials = mock_credentials
        mock_verify.return_value = {"email": "u@example.com", "exp": time.time() + 3600}

        request = self.factory.get("/gauth/login-callback?state=s&code=c")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "s"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/"
        # Simulate a stale idle stamp left over from a previously-expired session.
        stale = time.time() - 10_000
        session[SESSION_LAST_ACTIVE_KEY] = stale
        session.create()
        request.session = session

        callback(request)

        # Login time stamped fresh, and the idle clock moved forward past the
        # stale value so GOOGLE_SESSION_IDLE_TIMEOUT won't fire immediately.
        self.assertIn(SESSION_LOGIN_AT_KEY, request.session)
        self.assertGreater(request.session[SESSION_LAST_ACTIVE_KEY], stale)

        # And the fresh session must now pass the policy gate.
        from django_gauth.utilities import _within_session_policy

        self.assertTrue(_within_session_policy(request.session))

    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_restores_preexisting_relax_scope_env(
        self, mock_flow_class, mock_verify
    ):
        """A pre-existing OAUTHLIB_RELAX_TOKEN_SCOPE value is restored, not clobbered."""
        import os

        from django.contrib.sessions.backends.db import SessionStore
        from django_gauth.views import callback

        mock_flow_instance = MagicMock()
        mock_flow_class.return_value = mock_flow_instance
        mock_credentials = MagicMock()
        mock_credentials.token = "tok"
        mock_credentials.refresh_token = "rtok"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.scopes = settings.SCOPE
        mock_credentials.id_token = "id_tok"
        mock_flow_instance.credentials = mock_credentials
        mock_verify.return_value = {"email": "u@example.com", "exp": time.time() + 3600}

        request = self.factory.get("/gauth/login-callback?state=s&code=c")
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "s"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/"
        session.create()
        request.session = session

        prev = os.environ.get("OAUTHLIB_RELAX_TOKEN_SCOPE")
        os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "sentinel"
        try:
            callback(request)
            # The prior value must be restored after the token exchange.
            self.assertEqual(os.environ.get("OAUTHLIB_RELAX_TOKEN_SCOPE"), "sentinel")
        finally:
            if prev is None:
                os.environ.pop("OAUTHLIB_RELAX_TOKEN_SCOPE", None)
            else:
                os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = prev


# ============================================================
# utilities.py — revoke_google_token (v0.4.0 session lifecycle)
# ============================================================
class RevokeGoogleTokenTest(TestCase):
    """Cover utilities.revoke_google_token"""

    def test_empty_token_returns_false(self):
        from django_gauth.utilities import revoke_google_token

        self.assertFalse(revoke_google_token(""))

    @patch("django_gauth.utilities.google_requests.Request")
    def test_successful_revocation_returns_true(self, mock_request_cls):
        from django_gauth.utilities import revoke_google_token

        mock_transport = MagicMock()
        mock_transport.return_value = MagicMock(status=200)
        mock_request_cls.return_value = mock_transport

        self.assertTrue(revoke_google_token("some-refresh-token"))
        mock_transport.assert_called_once()

    @patch("django_gauth.utilities.google_requests.Request")
    def test_non_200_returns_false(self, mock_request_cls):
        from django_gauth.utilities import revoke_google_token

        mock_transport = MagicMock()
        mock_transport.return_value = MagicMock(status=400)
        mock_request_cls.return_value = mock_transport

        self.assertFalse(revoke_google_token("bad-token"))

    @patch("django_gauth.utilities.google_requests.Request")
    def test_transport_exception_returns_false(self, mock_request_cls):
        from django_gauth.utilities import revoke_google_token

        mock_transport = MagicMock()
        mock_transport.side_effect = Exception("network down")
        mock_request_cls.return_value = mock_transport

        self.assertFalse(revoke_google_token("some-token"))


# ============================================================
# utilities.py — get_credentials accessor (v0.4.0 session lifecycle)
# ============================================================
class GetCredentialsTest(TestCase):
    """Cover utilities.get_credentials"""

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, session):
        request = self.factory.get("/gauth/session")
        request.session = session
        return request

    def test_no_credentials_returns_none(self):
        from django_gauth.utilities import get_credentials

        result = get_credentials(self._request({}))
        self.assertIsNone(result)

    @patch("django_gauth.utilities.Credentials")
    def test_valid_session_returns_credentials(self, mock_credentials_class):
        from django_gauth.utilities import get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "tok",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["openid"],
            }
        }
        result = get_credentials(self._request(session))
        self.assertEqual(result, inst)
        # a valid session must NOT trigger a refresh
        inst.refresh.assert_not_called()

    @patch("django_gauth.utilities.id_token.verify_oauth2_token")
    @patch("django_gauth.utilities.google_requests.Request")
    @patch("django_gauth.utilities.Credentials")
    def test_expired_session_refreshes(
        self, mock_credentials_class, mock_request_cls, mock_verify
    ):
        from django_gauth.utilities import get_credentials

        inst = MagicMock()
        inst.valid = True
        inst.token = "new-access-token"
        inst.refresh_token = "rtok"
        inst.token_uri = "https://oauth2.googleapis.com/token"
        inst.scopes = ["openid"]
        mock_credentials_class.return_value = inst
        mock_verify.return_value = {
            "email": "user@example.com",
            "exp": time.time() + 3600,
        }

        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "stale",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["openid"],
            },
            "id_info": {"exp": time.time() - 100},  # expired
        }
        result = get_credentials(self._request(session))

        self.assertEqual(result, inst)
        inst.refresh.assert_called_once()
        # session must carry the freshly verified id_info forward
        self.assertEqual(session["id_info"]["email"], "user@example.com")
        self.assertGreater(session["id_info"]["exp"], time.time())

    @patch("django_gauth.utilities.id_token.verify_oauth2_token")
    @patch("django_gauth.utilities.google_requests.Request")
    @patch("django_gauth.utilities.Credentials")
    def test_expired_session_flags_real_session_modified(
        self, mock_credentials_class, mock_request_cls, mock_verify
    ):
        """A real Django session must be flagged ``modified`` after a refresh."""
        from django.contrib.sessions.backends.signed_cookies import SessionStore

        from django_gauth.utilities import get_credentials

        inst = MagicMock()
        inst.valid = True
        inst.token = "new-access-token"
        inst.refresh_token = "rtok"
        inst.token_uri = "https://oauth2.googleapis.com/token"
        inst.scopes = ["openid"]
        mock_credentials_class.return_value = inst
        mock_verify.return_value = {
            "email": "user@example.com",
            "exp": time.time() + 3600,
        }

        session = SessionStore()
        session[settings.CREDENTIALS_SESSION_KEY_NAME] = {
            "token": "stale",
            "refresh_token": "rtok",
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": ["openid"],
        }
        session["id_info"] = {"exp": time.time() - 100}  # expired
        session.modified = False  # reset flag after seeding

        result = get_credentials(self._request(session))

        self.assertEqual(result, inst)
        # our code path must re-flag the real session as modified
        self.assertTrue(session.modified)

    def test_expired_session_without_refresh_token_returns_none(self):
        from django_gauth.utilities import get_credentials

        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "stale",
                "refresh_token": "",  # nothing to refresh with
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["openid"],
            },
            "id_info": {"exp": time.time() - 100},  # expired
        }
        result = get_credentials(self._request(session))
        self.assertIsNone(result)

    @patch("django_gauth.utilities.google_requests.Request")
    @patch("django_gauth.utilities.Credentials")
    def test_refresh_failure_returns_none(
        self, mock_credentials_class, mock_request_cls
    ):
        from django_gauth.utilities import get_credentials

        inst = MagicMock()
        inst.valid = True
        inst.refresh.side_effect = Exception("refresh failed")
        mock_credentials_class.return_value = inst

        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "stale",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["openid"],
            },
            "id_info": {"exp": time.time() - 100},  # expired
        }
        result = get_credentials(self._request(session))
        self.assertIsNone(result)


# ============================================================
# utilities.py — session policy (v0.4.0)
#   GOOGLE_SESSION_AUTO_REFRESH / MAX_AGE / IDLE_TIMEOUT
# ============================================================
class SessionPolicyTest(TestCase):
    """Cover the configurable session-policy layer in get_credentials."""

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, session):
        request = self.factory.get("/gauth/session")
        request.session = session
        return request

    def _valid_session(self, **extra):
        session = {
            settings.CREDENTIALS_SESSION_KEY_NAME: {
                "token": "tok",
                "refresh_token": "rtok",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["openid"],
            },
            "id_info": {"exp": time.time() + 3600},  # not expired
        }
        session.update(extra)
        return session

    def _expired_session(self, **extra):
        session = self._valid_session()
        session["id_info"] = {"exp": time.time() - 100}  # expired
        session.update(extra)
        return session

    @override_settings(GOOGLE_SESSION_AUTO_REFRESH=False)
    @patch("django_gauth.utilities.Credentials")
    def test_auto_refresh_disabled_skips_refresh(self, mock_credentials_class):
        from django_gauth.utilities import get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        # token expired, refresh_token present — but refresh is switched off
        session = self._expired_session()
        result = get_credentials(self._request(session))

        self.assertIsNone(result)
        inst.refresh.assert_not_called()

    @override_settings(GOOGLE_SESSION_MAX_AGE=1800)
    @patch("django_gauth.utilities.Credentials")
    def test_max_age_exceeded_expires_valid_session(self, mock_credentials_class):
        from django_gauth.utilities import SESSION_LOGIN_AT_KEY, get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        # the token itself is still valid, but the session is older than the cap
        session = self._valid_session(**{SESSION_LOGIN_AT_KEY: time.time() - 3600})
        result = get_credentials(self._request(session))

        self.assertIsNone(result)
        inst.refresh.assert_not_called()

    @override_settings(GOOGLE_SESSION_MAX_AGE=3600)
    @patch("django_gauth.utilities.Credentials")
    def test_max_age_within_bounds_returns_credentials(self, mock_credentials_class):
        from django_gauth.utilities import SESSION_LOGIN_AT_KEY, get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        session = self._valid_session(**{SESSION_LOGIN_AT_KEY: time.time() - 100})
        result = get_credentials(self._request(session))

        self.assertEqual(result, inst)

    @override_settings(GOOGLE_SESSION_MAX_AGE=1800)
    @patch("django_gauth.utilities.Credentials")
    def test_max_age_missing_login_stamp_is_satisfied(self, mock_credentials_class):
        """A legacy session without a login stamp must not be locked out."""
        from django_gauth.utilities import get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        session = self._valid_session()  # no SESSION_LOGIN_AT_KEY
        result = get_credentials(self._request(session))

        self.assertEqual(result, inst)

    @override_settings(GOOGLE_SESSION_IDLE_TIMEOUT=900)
    @patch("django_gauth.utilities.Credentials")
    def test_idle_timeout_exceeded_expires_session(self, mock_credentials_class):
        from django_gauth.utilities import SESSION_LAST_ACTIVE_KEY, get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        session = self._valid_session(**{SESSION_LAST_ACTIVE_KEY: time.time() - 1000})
        result = get_credentials(self._request(session))

        self.assertIsNone(result)

    @override_settings(GOOGLE_SESSION_IDLE_TIMEOUT=1800)
    @patch("django_gauth.utilities.Credentials")
    def test_idle_timeout_touches_last_active(self, mock_credentials_class):
        from django_gauth.utilities import SESSION_LAST_ACTIVE_KEY, get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        old = time.time() - 100
        session = self._valid_session(**{SESSION_LAST_ACTIVE_KEY: old})
        result = get_credentials(self._request(session))

        self.assertEqual(result, inst)
        # a successful access must move the idle clock forward
        self.assertGreater(session[SESSION_LAST_ACTIVE_KEY], old)

    @override_settings(GOOGLE_SESSION_IDLE_TIMEOUT=1800)
    @patch("django_gauth.utilities.Credentials")
    def test_idle_timeout_flags_real_session_modified(self, mock_credentials_class):
        """Touching last-active on a real Django session flags it ``modified``."""
        from django.contrib.sessions.backends.signed_cookies import SessionStore

        from django_gauth.utilities import SESSION_LAST_ACTIVE_KEY, get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        session = SessionStore()
        session[settings.CREDENTIALS_SESSION_KEY_NAME] = {
            "token": "tok",
            "refresh_token": "rtok",
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": ["openid"],
        }
        session["id_info"] = {"exp": time.time() + 3600}
        session[SESSION_LAST_ACTIVE_KEY] = time.time() - 100
        session.modified = False  # reset flag after seeding

        result = get_credentials(self._request(session))

        self.assertEqual(result, inst)
        # the last-active write must re-flag the real session as modified
        self.assertTrue(session.modified)

    @patch("django_gauth.utilities.Credentials")
    def test_no_idle_timeout_does_not_write_last_active(self, mock_credentials_class):
        """With idle timeout off, no last-active key is written (no extra save)."""
        from django_gauth.utilities import SESSION_LAST_ACTIVE_KEY, get_credentials

        inst = MagicMock()
        inst.valid = True
        mock_credentials_class.return_value = inst

        session = self._valid_session()
        get_credentials(self._request(session))

        self.assertNotIn(SESSION_LAST_ACTIVE_KEY, session)


# ============================================================
# utilities.py — get_session_expiry (v0.4.0 landing-page visibility)
# ============================================================
class GetSessionExpiryTest(TestCase):
    """Cover utilities.get_session_expiry (effective deadline + policy)."""

    def test_empty_session_has_no_deadline(self):
        from django_gauth.utilities import get_session_expiry

        result = get_session_expiry({})
        self.assertIsNone(result["expires_at"])
        self.assertIsNone(result["policy"])
        self.assertFalse(result["expired"])

    def test_token_only_deadline(self):
        """With no policy configured, the Google token exp governs."""
        from django_gauth.utilities import get_session_expiry

        exp = time.time() + 3600
        result = get_session_expiry({"id_info": {"exp": exp}})
        self.assertEqual(result["expires_at"], exp)
        self.assertEqual(result["policy"], "token")
        self.assertFalse(result["expired"])

    @override_settings(GOOGLE_SESSION_MAX_AGE=300)
    def test_max_age_wins_over_token(self):
        from django_gauth.utilities import SESSION_LOGIN_AT_KEY, get_session_expiry

        now = time.time()
        session = {
            "id_info": {"exp": now + 3600},  # token far away
            SESSION_LOGIN_AT_KEY: now,  # max-age deadline = now + 300
        }
        result = get_session_expiry(session)
        self.assertAlmostEqual(result["expires_at"], now + 300, delta=1)
        self.assertEqual(result["policy"], "max_age")
        self.assertFalse(result["expired"])

    @override_settings(GOOGLE_SESSION_MAX_AGE=300, GOOGLE_SESSION_IDLE_TIMEOUT=60)
    def test_idle_wins_when_earliest(self):
        from django_gauth.utilities import (
            SESSION_LAST_ACTIVE_KEY,
            SESSION_LOGIN_AT_KEY,
            get_session_expiry,
        )

        now = time.time()
        session = {
            "id_info": {"exp": now + 3600},
            SESSION_LOGIN_AT_KEY: now,  # max-age = now + 300
            SESSION_LAST_ACTIVE_KEY: now,  # idle = now + 60 (earliest)
        }
        result = get_session_expiry(session)
        self.assertAlmostEqual(result["expires_at"], now + 60, delta=1)
        self.assertEqual(result["policy"], "idle")
        self.assertFalse(result["expired"])

    @override_settings(GOOGLE_SESSION_MAX_AGE=300)
    def test_expired_flag_set_when_deadline_passed(self):
        from django_gauth.utilities import SESSION_LOGIN_AT_KEY, get_session_expiry

        now = time.time()
        session = {
            "id_info": {"exp": now + 3600},
            SESSION_LOGIN_AT_KEY: now - 600,  # max-age deadline was 300s ago
        }
        result = get_session_expiry(session)
        self.assertEqual(result["policy"], "max_age")
        self.assertTrue(result["expired"])

    @override_settings(GOOGLE_SESSION_IDLE_TIMEOUT=60)
    def test_pure_read_does_not_mutate_session(self):
        """The calculator must not disturb the idle clock (no side effects)."""
        from django_gauth.utilities import (
            SESSION_LAST_ACTIVE_KEY,
            get_session_expiry,
        )

        now = time.time()
        session = {
            "id_info": {"exp": now + 3600},
            SESSION_LAST_ACTIVE_KEY: now - 10,
        }
        snapshot = dict(session)
        get_session_expiry(session)
        self.assertEqual(session, snapshot)


# ============================================================
# views.py — logout view (v0.4.0 session lifecycle)
# ============================================================
class LogoutViewTest(TestCase):
    """Cover views.logout"""

    def setUp(self):
        self.client = Client()

    def _seed_credentials(self):
        session = self.client.session
        session[settings.CREDENTIALS_SESSION_KEY_NAME] = {
            "token": "access-tok",
            "refresh_token": "refresh-tok",
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": ["openid"],
        }
        session.save()

    @patch("django_gauth.views.revoke_google_token")
    def test_logout_json_response(self, mock_revoke):
        import json

        self._seed_credentials()
        response = self.client.get(reverse("django_gauth:logout") + "?response=json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"status": "logged_out"})
        # the refresh_token is preferred for revocation
        mock_revoke.assert_called_once_with("refresh-tok")
        # session must be cleared
        self.assertNotIn(settings.CREDENTIALS_SESSION_KEY_NAME, self.client.session)

    def test_logout_redirect_response_default(self):
        response = self.client.get(reverse("django_gauth:logout"))
        self.assertEqual(response.status_code, 302)

    def test_logout_invalid_response_returns_400(self):
        response = self.client.get(reverse("django_gauth:logout") + "?response=xml")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid response type", response.content)

    @override_settings(GOOGLE_AUTH_LOGOUT_REDIRECT_URL="http://testserver/bye/")
    def test_logout_custom_redirect_url(self):
        response = self.client.get(reverse("django_gauth:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "http://testserver/bye/")

    @override_settings(GOOGLE_TOKEN_REVOKE_ON_LOGOUT=False)
    @patch("django_gauth.views.revoke_google_token")
    def test_logout_revocation_disabled(self, mock_revoke):
        self._seed_credentials()
        response = self.client.get(reverse("django_gauth:logout") + "?response=json")
        self.assertEqual(response.status_code, 200)
        mock_revoke.assert_not_called()


# ============================================================
# views.py — session_status probe (v0.4.0 session lifecycle)
# ============================================================
class SessionStatusViewTest(TestCase):
    """Cover views.session_status"""

    def setUp(self):
        self.client = Client()

    @patch("django_gauth.views.get_credentials")
    def test_session_authenticated(self, mock_get_credentials):
        import json

        mock_get_credentials.return_value = MagicMock()  # non-None → authenticated
        session = self.client.session
        session["id_info"] = {
            "email": "user@example.com",
            "name": "Test User",
            "iss": "accounts.google.com",
            "azp": "abc",
            "aud": "xyz",
            "sub": "1234",
        }
        session.save()

        response = self.client.get(reverse("django_gauth:session"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user"]["email"], "user@example.com")
        # opaque claims must be stripped
        self.assertNotIn("iss", data["user"])
        self.assertNotIn("azp", data["user"])
        self.assertNotIn("aud", data["user"])
        self.assertNotIn("sub", data["user"])

    @patch("django_gauth.views.get_credentials")
    def test_session_unauthenticated(self, mock_get_credentials):
        import json

        mock_get_credentials.return_value = None
        response = self.client.get(reverse("django_gauth:session"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["authenticated"])
        self.assertIsNone(data["user"])


# ============================================================
# utilities.py — get_or_create_user_from_id_info (v0.3.0 User integration)
# ============================================================
def _test_user_mapper(id_info, user, created):  # noqa: ARG001
    """Module-level mapper used by the GOOGLE_USER_MAPPER test (dotted-path)."""
    user.first_name = "MAPPED"
    user.last_name = "created" if created else "existing"


class GetOrCreateUserTest(TestCase):
    """Cover utilities.get_or_create_user_from_id_info (model-free get-or-create)."""

    def _verified(self, **extra):
        info = {
            "email": "alice@example.com",
            "email_verified": True,
            "given_name": "Alice",
            "family_name": "Smith",
        }
        info.update(extra)
        return info

    def test_empty_id_info_returns_none(self):
        from django_gauth.utilities import get_or_create_user_from_id_info

        self.assertIsNone(get_or_create_user_from_id_info({}))

    @override_settings(GOOGLE_USER_REQUIRE_VERIFIED_EMAIL=True)
    def test_unverified_email_rejected(self):
        from django_gauth.utilities import get_or_create_user_from_id_info

        result = get_or_create_user_from_id_info(self._verified(email_verified=False))
        self.assertIsNone(result)

    @override_settings(GOOGLE_USER_REQUIRE_VERIFIED_EMAIL=False)
    def test_unverified_allowed_when_not_required(self):
        from django_gauth.utilities import get_or_create_user_from_id_info

        user = get_or_create_user_from_id_info(self._verified(email_verified=False))
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "alice@example.com")

    def test_missing_email_returns_none(self):
        from django_gauth.utilities import get_or_create_user_from_id_info

        self.assertIsNone(get_or_create_user_from_id_info({"email_verified": True}))

    def test_creates_user_when_absent(self):
        from django.contrib.auth import get_user_model

        from django_gauth.utilities import get_or_create_user_from_id_info

        user_model = get_user_model()
        self.assertFalse(
            user_model.objects.filter(email="alice@example.com").exists()
        )

        user = get_or_create_user_from_id_info(self._verified())

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "alice@example.com")
        self.assertEqual(user.username, "alice")
        # default mapper populated the name fields
        self.assertEqual(user.first_name, "Alice")
        self.assertEqual(user.last_name, "Smith")
        # OAuth users authenticate via Google — never a local password
        self.assertFalse(user.has_usable_password())

    def test_returns_existing_user_without_creating(self):
        from django.contrib.auth import get_user_model

        from django_gauth.utilities import get_or_create_user_from_id_info

        user_model = get_user_model()
        existing = user_model.objects.create(
            username="alice", email="alice@example.com"
        )

        user = get_or_create_user_from_id_info(self._verified())

        self.assertEqual(user.pk, existing.pk)
        self.assertEqual(
            user_model.objects.filter(email="alice@example.com").count(), 1
        )

    def test_case_insensitive_match(self):
        from django.contrib.auth import get_user_model

        from django_gauth.utilities import get_or_create_user_from_id_info

        user_model = get_user_model()
        existing = user_model.objects.create(
            username="alice", email="Alice@Example.com"
        )

        user = get_or_create_user_from_id_info(
            self._verified(email="alice@example.com")
        )
        self.assertEqual(user.pk, existing.pk)

    @override_settings(GOOGLE_USER_AUTO_CREATE=False)
    def test_no_create_when_disabled_returns_none(self):
        from django_gauth.utilities import get_or_create_user_from_id_info

        self.assertIsNone(get_or_create_user_from_id_info(self._verified()))

    def test_username_collision_is_uniquified(self):
        from django.contrib.auth import get_user_model

        from django_gauth.utilities import get_or_create_user_from_id_info

        user_model = get_user_model()
        # occupy the natural username 'alice' with a different account
        user_model.objects.create(username="alice", email="someone-else@example.com")

        user = get_or_create_user_from_id_info(
            self._verified(email="alice@example.com")
        )
        self.assertEqual(user.email, "alice@example.com")
        self.assertNotEqual(user.username, "alice")
        self.assertTrue(user.username.startswith("alice"))

    @override_settings(GOOGLE_USER_LOOKUP_FIELD="username")
    def test_custom_lookup_field_missing_value_returns_none(self):
        from django_gauth.utilities import get_or_create_user_from_id_info

        # id_info carries no 'username' claim → no lookup value → refuse sign-in
        self.assertIsNone(get_or_create_user_from_id_info(self._verified()))

    @override_settings(
        GOOGLE_USER_MAPPER="tests.test_coverage_boost._test_user_mapper"
    )
    def test_custom_mapper_applied(self):
        from django_gauth.utilities import get_or_create_user_from_id_info

        user = get_or_create_user_from_id_info(self._verified())
        self.assertEqual(user.first_name, "MAPPED")
        self.assertEqual(user.last_name, "created")

    def test_build_new_user_email_as_username_branch(self):
        # Directly exercise the "email is the username" branch of _build_new_user
        from django_gauth.utilities import _build_new_user

        fake_model = MagicMock()
        fake_model.USERNAME_FIELD = "email"
        fake_model.EMAIL_FIELD = "email"

        _build_new_user(fake_model, "eva@example.com")

        fake_model.assert_called_once_with(email="eva@example.com")
        fake_model.return_value.set_unusable_password.assert_called_once()


# ============================================================
# backends.py — GoogleAuthBackend (v0.3.0 User integration)
# ============================================================
class GoogleAuthBackendTest(TestCase):
    """Cover backends.GoogleAuthBackend"""

    def test_authenticate_without_id_info_opts_out(self):
        from django_gauth.backends import GoogleAuthBackend

        # No id_info → backend must stay passive so ModelBackend can handle it
        self.assertIsNone(GoogleAuthBackend().authenticate(None, id_info=None))

    @patch("django_gauth.backends.get_or_create_user_from_id_info")
    def test_authenticate_returns_active_user(self, mock_goc):
        from django_gauth.backends import GoogleAuthBackend

        user = MagicMock()
        user.is_active = True
        mock_goc.return_value = user

        result = GoogleAuthBackend().authenticate(None, id_info={"email": "a@b.com"})
        self.assertIs(result, user)

    @patch("django_gauth.backends.get_or_create_user_from_id_info")
    def test_authenticate_returns_none_when_user_refused(self, mock_goc):
        from django_gauth.backends import GoogleAuthBackend

        mock_goc.return_value = None
        result = GoogleAuthBackend().authenticate(None, id_info={"email": "a@b.com"})
        self.assertIsNone(result)

    @patch("django_gauth.backends.get_or_create_user_from_id_info")
    def test_authenticate_rejects_inactive_user(self, mock_goc):
        from django_gauth.backends import GoogleAuthBackend

        user = MagicMock()
        user.is_active = False
        mock_goc.return_value = user

        result = GoogleAuthBackend().authenticate(None, id_info={"email": "a@b.com"})
        self.assertIsNone(result)

    def test_get_user_returns_existing(self):
        from django.contrib.auth import get_user_model

        from django_gauth.backends import GoogleAuthBackend

        user_model = get_user_model()
        user = user_model.objects.create(username="bob", email="bob@example.com")

        self.assertEqual(GoogleAuthBackend().get_user(user.pk), user)

    def test_get_user_missing_returns_none(self):
        from django_gauth.backends import GoogleAuthBackend

        self.assertIsNone(GoogleAuthBackend().get_user(999999))


# ============================================================
# views.py — callback + Django User integration (v0.3.0, Phase 2)
# ============================================================
class CallbackUserIntegrationTest(TestCase):
    """Cover views.callback's opt-in authenticate()/login() seam."""

    def setUp(self):
        self.factory = RequestFactory()

    def _mock_flow(self, mock_flow_class):
        mock_flow_instance = MagicMock()
        mock_flow_class.return_value = mock_flow_instance
        creds = MagicMock()
        creds.token = "access_token"
        creds.refresh_token = "refresh_token"
        creds.token_uri = "https://oauth2.googleapis.com/token"
        creds.client_id = settings.GOOGLE_CLIENT_ID
        creds.client_secret = settings.GOOGLE_CLIENT_SECRET
        creds.scopes = ["openid"]
        creds.id_token = "fake_id_token"
        mock_flow_instance.credentials = creds
        return mock_flow_instance

    def _request(self):
        from django.contrib.auth.models import AnonymousUser
        from django.contrib.sessions.backends.db import SessionStore

        request = self.factory.get(
            "/gauth/login-callback?state=test_state&code=test_code"
        )
        session = SessionStore()
        session[settings.STATE_KEY_NAME] = "test_state"
        session[settings.FINAL_REDIRECT_KEY_NAME] = "http://testserver/gauth/"
        session.create()
        request.session = session
        request.user = AnonymousUser()  # emulate AuthenticationMiddleware
        return request

    @override_settings(
        GOOGLE_USER_INTEGRATION=True,
        AUTHENTICATION_BACKENDS=[
            "django_gauth.backends.GoogleAuthBackend",
            "django.contrib.auth.backends.ModelBackend",
        ],
    )
    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_logs_in_django_user_when_integrated(
        self, mock_flow_class, mock_verify
    ):
        from django.contrib.auth import SESSION_KEY, get_user_model

        from django_gauth.views import callback

        self._mock_flow(mock_flow_class)
        mock_verify.return_value = {
            "email": "carol@example.com",
            "email_verified": True,
            "given_name": "Carol",
            "family_name": "Jones",
            "exp": time.time() + 3600,
        }
        request = self._request()

        response = callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "http://testserver/gauth/")
        # A real auth_user was created + a Django auth session was opened.
        user = get_user_model().objects.get(email="carol@example.com")
        self.assertEqual(request.session[SESSION_KEY], str(user.pk))
        self.assertEqual(request.user, user)
        # Google session state still lives alongside the Django auth session.
        self.assertIn("id_info", request.session)
        self.assertIn(settings.CREDENTIALS_SESSION_KEY_NAME, request.session)

    @override_settings(
        GOOGLE_USER_INTEGRATION=True,
        GOOGLE_USER_REQUIRE_VERIFIED_EMAIL=True,
        AUTHENTICATION_BACKENDS=[
            "django_gauth.backends.GoogleAuthBackend",
            "django.contrib.auth.backends.ModelBackend",
        ],
    )
    @patch("django_gauth.views.id_token.verify_oauth2_token")
    @patch("django_gauth.views.Flow.from_client_config")
    def test_callback_skips_login_when_user_refused(
        self, mock_flow_class, mock_verify
    ):
        from django.contrib.auth import SESSION_KEY

        from django_gauth.views import callback

        self._mock_flow(mock_flow_class)
        # Unverified email → backend returns None → no login, flow still completes.
        mock_verify.return_value = {
            "email": "dan@example.com",
            "email_verified": False,
            "exp": time.time() + 3600,
        }
        request = self._request()

        response = callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(SESSION_KEY, request.session)
        # Google session state is still written even though no Django login.
        self.assertIn("id_info", request.session)
        self.assertIn(settings.CREDENTIALS_SESSION_KEY_NAME, request.session)


# ============================================================
# views.py — logout + Django User integration (v0.3.0, Phase 2)
# ============================================================
class LogoutUserIntegrationTest(TestCase):
    """Cover views.logout routing through auth.logout() when integrated."""

    def setUp(self):
        self.client = Client()

    @override_settings(GOOGLE_USER_INTEGRATION=True)
    def test_logout_clears_django_auth_session(self):
        from django.contrib.auth import SESSION_KEY, get_user_model

        user = get_user_model().objects.create(
            username="erin", email="erin@example.com"
        )
        self.client.force_login(user)
        # sanity: the Django auth session key exists before logout
        self.assertIn(SESSION_KEY, self.client.session)

        response = self.client.get(reverse("django_gauth:logout") + "?response=json")
        self.assertEqual(response.status_code, 200)
        # auth.logout() flushed the session → Django auth key is gone.
        self.assertNotIn(SESSION_KEY, self.client.session)


# ============================================================
# views.py — session_status user_id field (v0.3.0, ADR-7, Phase 2)
# ============================================================
class SessionStatusUserIdTest(TestCase):
    """Cover the ADR-7 top-level user_id field in session_status."""

    def setUp(self):
        self.client = Client()

    @patch("django_gauth.views.get_credentials")
    def test_user_id_present_and_null_when_integration_off(self, mock_get_credentials):
        import json

        mock_get_credentials.return_value = MagicMock()  # Google-authenticated
        session = self.client.session
        session["id_info"] = {"email": "f@example.com"}
        session.save()

        response = self.client.get(reverse("django_gauth:session"))
        data = json.loads(response.content)
        self.assertTrue(data["authenticated"])
        self.assertIn("user_id", data)  # ADR-7: always present
        self.assertIsNone(data["user_id"])  # ...null unless integrated + authed

    @override_settings(GOOGLE_USER_INTEGRATION=True)
    @patch("django_gauth.views.get_credentials")
    def test_user_id_null_when_integrated_but_anonymous(self, mock_get_credentials):
        import json

        mock_get_credentials.return_value = None  # unauthenticated
        response = self.client.get(reverse("django_gauth:session"))
        data = json.loads(response.content)
        self.assertFalse(data["authenticated"])
        self.assertIn("user_id", data)
        self.assertIsNone(data["user_id"])

    @override_settings(GOOGLE_USER_INTEGRATION=True)
    @patch("django_gauth.views.get_credentials")
    def test_user_id_populated_when_integrated_and_authed(self, mock_get_credentials):
        import json

        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create(
            username="gwen", email="gwen@example.com"
        )
        self.client.force_login(user)
        mock_get_credentials.return_value = MagicMock()
        session = self.client.session
        session["id_info"] = {"email": "gwen@example.com"}
        session.save()

        response = self.client.get(reverse("django_gauth:session"))
        data = json.loads(response.content)
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user_id"], user.pk)

    @override_settings(GOOGLE_USER_INTEGRATION=True)
    @patch("django_gauth.views.get_credentials")
    def test_user_id_set_even_without_google_credentials(self, mock_get_credentials):
        """Django-authenticated (e.g. admin) but no Google session → still authenticated."""
        import json

        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create(
            username="hank", email="hank@example.com"
        )
        self.client.force_login(user)
        mock_get_credentials.return_value = None  # no Google credentials

        response = self.client.get(reverse("django_gauth:session"))
        data = json.loads(response.content)
        # With integration ON, authenticated mirrors request.user.is_authenticated
        # (matching @gauth_required / @login_required), not the Google cred state.
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user_id"], user.pk)


# ============================================================
# decorators.py — gauth_required (v0.3.0 Phase 4)
# ============================================================
def _protected_ok_view(request):  # noqa: ARG001
    """Dummy protected view used by the decorator/mixin tests."""
    return HttpResponse("ok")


class GauthRequiredDecoratorTest(TestCase):
    """Cover decorators.gauth_required (dual-mode + response=redirect|json)."""

    def setUp(self):
        self.factory = RequestFactory()

    @patch("django_gauth.decorators.get_credentials")
    def test_allows_authenticated_session(self, mock_get_creds):
        from django_gauth.decorators import gauth_required

        mock_get_creds.return_value = object()  # non-None → authenticated
        protected = gauth_required(_protected_ok_view)  # bare usage
        request = self.factory.get("/protected/")
        request.session = {}

        response = protected(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    @patch("django_gauth.decorators.get_credentials")
    def test_redirects_unauthenticated(self, mock_get_creds):
        from django_gauth.decorators import gauth_required

        mock_get_creds.return_value = None
        protected = gauth_required(_protected_ok_view)
        request = self.factory.get("/protected/")
        request.session = {}

        response = protected(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("django_gauth:login"), response.url)

    @patch("django_gauth.decorators.get_credentials")
    def test_json_response_when_unauthenticated(self, mock_get_creds):
        import json

        from django_gauth.decorators import gauth_required

        mock_get_creds.return_value = None
        protected = gauth_required(response="json")(_protected_ok_view)  # parameterised
        request = self.factory.get("/protected/")
        request.session = {}

        response = protected(request)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(json.loads(response.content)["authenticated"])

    @patch("django_gauth.decorators.get_credentials")
    def test_custom_login_url(self, mock_get_creds):
        from django_gauth.decorators import gauth_required

        mock_get_creds.return_value = None
        protected = gauth_required(login_url="/accounts/login/")(_protected_ok_view)
        request = self.factory.get("/protected/")
        request.session = {}

        response = protected(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/")

    def test_invalid_response_raises(self):
        from django_gauth.decorators import gauth_required

        with self.assertRaises(ValueError):
            gauth_required(response="xml")

    @override_settings(GOOGLE_USER_INTEGRATION=True)
    def test_integration_allows_authenticated_user(self):
        from django_gauth.decorators import gauth_required

        protected = gauth_required(_protected_ok_view)
        request = self.factory.get("/protected/")
        user = MagicMock()
        user.is_authenticated = True
        request.user = user
        request.session = {}

        response = protected(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(GOOGLE_USER_INTEGRATION=True)
    def test_integration_blocks_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser

        from django_gauth.decorators import gauth_required

        protected = gauth_required(response="json")(_protected_ok_view)
        request = self.factory.get("/protected/")
        request.user = AnonymousUser()

        response = protected(request)
        self.assertEqual(response.status_code, 401)

    @override_settings(GOOGLE_USER_INTEGRATION=True, GOOGLE_SESSION_MAX_AGE=300)
    def test_integration_blocks_expired_session_policy(self):
        """Session-policy caps are enforced even when request.user is valid."""
        import time

        from django_gauth.decorators import gauth_required
        from django_gauth.utilities import SESSION_LOGIN_AT_KEY

        protected = gauth_required(response="json")(_protected_ok_view)
        request = self.factory.get("/protected/")
        user = MagicMock()
        user.is_authenticated = True
        request.user = user
        # Session has a login timestamp that exceeds GOOGLE_SESSION_MAX_AGE.
        request.session = {SESSION_LOGIN_AT_KEY: time.time() - 600}

        response = protected(request)
        self.assertEqual(response.status_code, 401)

    @patch("django_gauth.decorators.get_credentials")
    @override_settings(GOOGLE_SESSION_MAX_AGE=300)
    def test_session_policy_enforced_via_get_credentials(self, mock_get_creds):
        """Non-integration path delegates policy enforcement to get_credentials."""
        from django_gauth.decorators import gauth_required

        # get_credentials returns None when session policy has expired.
        mock_get_creds.return_value = None
        protected = gauth_required(response="json")(_protected_ok_view)
        request = self.factory.get("/protected/")
        request.session = {}

        response = protected(request)
        self.assertEqual(response.status_code, 401)
        mock_get_creds.assert_called_once_with(request)


class GauthRequiredMixinTest(TestCase):
    """Cover decorators.GauthRequiredMixin (dual-mode dispatch guard)."""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_view(self, **attrs):
        from django.views import View

        from django_gauth.decorators import GauthRequiredMixin

        class _Protected(GauthRequiredMixin, View):
            def get(self, request, *args, **kwargs):  # noqa: ARG002
                return HttpResponse("ok")

        for key, value in attrs.items():
            setattr(_Protected, key, value)
        return _Protected.as_view()

    @patch("django_gauth.decorators.get_credentials")
    def test_mixin_allows_authenticated(self, mock_get_creds):
        mock_get_creds.return_value = object()
        view = self._make_view()
        request = self.factory.get("/p/")
        request.session = {}

        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    @patch("django_gauth.decorators.get_credentials")
    def test_mixin_redirects_unauthenticated(self, mock_get_creds):
        mock_get_creds.return_value = None
        view = self._make_view()
        request = self.factory.get("/p/")
        request.session = {}

        response = view(request)
        self.assertEqual(response.status_code, 302)

    @patch("django_gauth.decorators.get_credentials")
    def test_mixin_json_unauthenticated(self, mock_get_creds):
        mock_get_creds.return_value = None
        view = self._make_view(gauth_response="json")
        request = self.factory.get("/p/")
        request.session = {}

        response = view(request)
        self.assertEqual(response.status_code, 401)

    def test_mixin_invalid_response_raises(self):
        view = self._make_view(gauth_response="xml")
        request = self.factory.get("/p/")
        request.session = {}

        with self.assertRaises(ValueError):
            view(request)

    @override_settings(GOOGLE_USER_INTEGRATION=True)
    def test_mixin_integration_blocks_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        view = self._make_view(gauth_response="json")
        request = self.factory.get("/p/")
        request.user = AnonymousUser()

        response = view(request)
        self.assertEqual(response.status_code, 401)

