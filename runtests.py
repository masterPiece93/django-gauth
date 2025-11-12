# my_reusable_app/runtests.py
import os
import sys

import django   # pylint: disable=import-error
from django.conf import settings    # pylint: disable=import-error
from django.test.runner import DiscoverRunner   # pylint: disable=import-error

# from devPlatform.devPlatform import settings as SettingsHub
# SettingsHub.ROOT_URLCONF = 'devPlatform.devPlatform.urls'
from tests import test_settings as SettingsHub

# Configure minimal settings for testing
settings.configure(
    SECRET_KEY = 'sample-insecure-test-secret-key',
    DEBUG=True,
    ALLOWED_HOSTS = ["*"],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    INSTALLED_APPS=SettingsHub.INSTALLED_APPS,  # pylint: disable=no-member
    MIDDLEWARE=SettingsHub.MIDDLEWARE,  # pylint: disable=no-member
    TEMPLATES=SettingsHub.TEMPLATES,    # pylint: disable=no-member
    ROOT_URLCONF = SettingsHub.ROOT_URLCONF, # pylint: disable=no-member
    USE_TZ = SettingsHub.USE_TZ,    # pylint: disable=no-member
    STATIC_URL = SettingsHub.STATIC_URL,    # pylint: disable=no-member
    DEFAULT_AUTO_FIELD = SettingsHub.DEFAULT_AUTO_FIELD,    # pylint: disable=no-member
    # Gauth App Variables
    GOOGLE_CLIENT_ID=SettingsHub.GOOGLE_CLIENT_ID,  # pylint: disable=no-member
    GOOGLE_CLIENT_SECRET=SettingsHub.GOOGLE_CLIENT_SECRET,  # pylint: disable=no-member
    GOOGLE_AUTH_FINAL_REDIRECT_URL=SettingsHub.GOOGLE_AUTH_FINAL_REDIRECT_URL,  # pylint: disable=no-member
    CREDENTIALS_SESSION_KEY_NAME=SettingsHub.CREDENTIALS_SESSION_KEY_NAME,  # pylint: disable=no-member
    STATE_KEY_NAME=SettingsHub.STATE_KEY_NAME,  # pylint: disable=no-member
    SCOPE=SettingsHub.SCOPE,    # pylint: disable=no-member
    # DJANGO_GAUTH_UI_CONFIG=devPlatformSettings.DJANGO_GAUTH_UI_CONFIG,
)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # :local-development

django.setup()

def run_tests():
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['tests']) # Specify your app's test package
    # sys.exit(bool(failures))
    return failures

if __name__ == '__main__':
    # Export ENV_PATH for different env file
    # Export ENV if ENV_PATH is not set
    from coverage import Coverage

    # Initialize Coverage
    cov = Coverage(source=['src'], omit=['*migrations*', '*tests*']) # Customize source and omit
    cov.start()
    failures=run_tests()
    # Stop Coverage and generate report
    cov.stop()
    cov.save()
    cov.report()
    cov.html_report(directory='htmlcov')

    sys.exit(bool(failures))
