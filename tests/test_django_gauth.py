import sys
from importlib import import_module, reload

import django
from django.conf import settings
from django.test import TestCase, override_settings
from django.test.client import Client
from django.urls import clear_url_caches, reverse

from tests import env

# @pytest.fixture(scope="session")
# def django_version():
#     """A session-scoped fixture that returns the Django version information."""
#     return django.get_version()

# @pytest.fixture(scope="session")
# def python_version():
#     """A session-scoped fixture that returns the Python version information."""
#     version = sys.version_info
#     print(f"\nPython version in session fixture: {version.major}.{version.minor}.{version.micro}")
#     return version

# @pytest.fixture(scope="session")
# def status_file(tmp_path_factory):
#     """
#     Fixture to provide a file object for recording test statuses.
#     The file is created in a temporary directory and closed at the end of the session.
#     """
#     file_path = tmp_path_factory.mktemp("test_status") / "test_results.txt"
#     with open(file_path, "w") as f:
#         f.write("Test Status Report:\n")
    
#     # Open the file again in append mode for subsequent writes
#     file_handle = open(file_path, "a")
#     yield file_handle
#     file_handle.close()

# def test_django_version_fixture(django_version, python_version, status_file):
    
#     status_file.write(
#         f"Django version from fixture: {django_version=}"
#         f"Django version from fixture: {python_version.major}.{python_version.minor}.{python_version.micro}"
#     )
#     if python_version.major == 3 and python_version.minor <= 9:
#         assert django_version.startswith("3.") or django_version.startswith("4.") # Example: Check if Django is a 4.x version
#     if python_version.major == 3 and python_version.minor > 9:
#         assert django_version.startswith("5.") or django_version.startswith("4.") # Example: Check if Django is a 5.x version

class GeneralTest(TestCase):
    """
    TestSuite for Generic Tests
    """
    def test_oauth2_env(self):
        self.assertEqual(settings.GOOGLE_CLIENT_ID, env.str("GOOGLE_CLIENT_ID"))
        self.assertEqual(settings.GOOGLE_CLIENT_SECRET, env.str("GOOGLE_CLIENT_SECRET"))

    # def test_debug(self):
    #     self.assertTrue(settings.DEBUG)

    def test_access_settings(self):
        # Access a specific setting
        debug_status = settings.DEBUG
        self.assertIsInstance(debug_status, bool)
        self.assertEqual(debug_status, False) # TestRunner Keeps it False

        # Access a list or dictionary setting
        installed_apps = settings.INSTALLED_APPS
        self.assertIn('django.contrib.admin', installed_apps)

class IndexViewTest(TestCase):
    """
    TestSuite for Landing Page
    """
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse('django_gauth:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        self.assertContains(response, "Gauth Application") # Check for content in the response


class LoginViewTest(TestCase):
    """
    TestSuite for Login Endpoint
    """
    def setUp(self):
        self.client = Client()

    def test_login(self):
        response = self.client.get(reverse('django_gauth:login'))
        self.assertEqual(response.status_code, 302) # Example for a redirect
        assert 'https://accounts.google.com/o/oauth2/v2/auth' in response.url
        # Further assertions based on your view's logic

@override_settings(DEBUG=True)
@override_settings(ROOT_URLCONF='devPlatform.devPlatform.urls')
class DebugApiTest(TestCase):
    """
    TestSuite for Debug Endpoint
    """
    def setUp(self):
        self.client = Client()

    def reload_urlconf(self, urlconf=None):
        clear_url_caches()
        if urlconf is None:
            urlconf = settings.ROOT_URLCONF
        if urlconf in sys.modules:
            reload(sys.modules[urlconf])
        else:
            import_module(urlconf)

    def test_gauth_debug(self):
        self.reload_urlconf()
        self.assertTrue(settings.DEBUG)
        # response = self.client.get(reverse('django_gauth:debug'))
        # self.assertEqual(response.status_code, 200)
