# my_reusable_app/runtests.py
import os
import sys

import django
from django.conf import settings

from devPlatform.devPlatform import settings as devPlatformSettings

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
    INSTALLED_APPS=devPlatformSettings.INSTALLED_APPS,
    MIDDLEWARE=devPlatformSettings.MIDDLEWARE,
    TEMPLATES=devPlatformSettings.TEMPLATES,
    ROOT_URLCONF = 'devPlatform.devPlatform.urls', # Point to your test URLs
    USE_TZ = devPlatformSettings.USE_TZ,
    STATIC_URL = devPlatformSettings.STATIC_URL,
    DEFAULT_AUTO_FIELD = devPlatformSettings.DEFAULT_AUTO_FIELD,
    # Gauth App Variables
    GOOGLE_CLIENT_ID=devPlatformSettings.GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET=devPlatformSettings.GOOGLE_CLIENT_SECRET,
    GOOGLE_AUTH_FINAL_REDIRECT_URL=devPlatformSettings.GOOGLE_AUTH_FINAL_REDIRECT_URL,
    CREDENTIALS_SESSION_KEY_NAME=devPlatformSettings.CREDENTIALS_SESSION_KEY_NAME,
    STATE_KEY_NAME=devPlatformSettings.STATE_KEY_NAME,
    SCOPE=devPlatformSettings.SCOPE,
    # DJANGO_GAUTH_UI_CONFIG=devPlatformSettings.DJANGO_GAUTH_UI_CONFIG,
)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # :local-development

django.setup()

from django.test.runner import DiscoverRunner


def run_tests():
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['tests']) # Specify your app's test package
    sys.exit(bool(failures))

if __name__ == '__main__':
    # Export ENV_PATH for different env file
    run_tests()
