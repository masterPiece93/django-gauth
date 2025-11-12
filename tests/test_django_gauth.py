import sys
from importlib import import_module, reload

from django.conf import settings    # pylint: disable=import-error
from django.test import TestCase, override_settings # pylint: disable=import-error
from django.test.client import Client   # pylint: disable=import-error
from django.urls import clear_url_caches, reverse   # pylint: disable=import-error

from tests import env

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
