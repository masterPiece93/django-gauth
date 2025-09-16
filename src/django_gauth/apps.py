from django.apps import AppConfig   # pylint: disable=E0401
from django.core.checks import register, Tags as DjangoTags, Warning, Info
from django_gauth._checks import *
from django_gauth import defaults
import warnings; warnings.simplefilter('default')

class Tags(DjangoTags):
    """Extending with Custom Tags
    
    NOTE : Do this if none of the existing tags work for you:
    https://docs.djangoproject.com/en/3.1/ref/checks/#builtin-tags
    """
    django_gauth_compatibility = 'django_gauth_compatibility'


# pylint: disable=R0903
class DjangoGauthConfig(AppConfig):
    """
    App Configurator @ django_gauth
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_gauth"

    def ready(self):
        register(Tags.compatibility)(check_project_middlewares)
        register(Tags.django_gauth_compatibility)(check_project_settings)

    @register(Tags.django_gauth_compatibility)
    def set_defaults(app_configs, **kwargs):
        errors = []
        if not hasattr(settings, "SCOPE"):
            setattr(settings, "SCOPE", [])
            
            errors.append(
                Warning(
                    "SCOPE setting is not defined. Defaulting to `[]`. It may affect the normal flow of oauth and might not run as expected . Please rectify ASAP.",
                    hint=("See https://masterpiece93.github.io/django-gauth/settings/ for more information"),
                    id=f"{DjangoGauthConfig.name}.E004" # TODO : define it consolidatedly in ErrorCodes
                                                        # TODO : update the docs with /settings section
                                                        #       with reference to this section
                )
            )

        if not hasattr(settings, "GOOGLE_AUTH_FINAL_REDIRECT_URL"):
            setattr(settings, "GOOGLE_AUTH_FINAL_REDIRECT_URL", defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL)
            _msg = f"GOOGLE_AUTH_FINAL_REDIRECT_URL settings is not defined. Defaulting to `{defaults.GOOGLE_AUTH_FINAL_REDIRECT_URL}`"
            warnings.warn(_msg)
        else:
            if not settings.GOOGLE_AUTH_FINAL_REDIRECT_URL:
                _msg = f"GOOGLE_AUTH_FINAL_REDIRECT_URL setting is set to `{settings.GOOGLE_AUTH_FINAL_REDIRECT_URL}` which is logically incorrect."
                info=Info(
                    _msg
                )
                errors.append(info)
        if not hasattr(settings, "CREDENTIALS_SESSION_KEY_NAME"):
            setattr(settings, "CREDENTIALS_SESSION_KEY_NAME", defaults.CREDENTIALS_SESSION_KEY_NAME)
            _msg = f"CREDENTIALS_SESSION_KEY_NAME settings is not defined. Defaulting to `{defaults.CREDENTIALS_SESSION_KEY_NAME}`"
            warnings.warn(_msg)
        else:
            if not settings.CREDENTIALS_SESSION_KEY_NAME:
                _msg = f"CREDENTIALS_SESSION_KEY_NAME setting is set to `{settings.CREDENTIALS_SESSION_KEY_NAME}` which is logically incorrect."
                info=Info(
                    _msg
                )
                errors.append(info)
        if not hasattr(settings, "STATE_KEY_NAME"):
            setattr(settings, "STATE_KEY_NAME", defaults.STATE_KEY_NAME)
            _msg = f"STATE_KEY_NAME settings is not defined. Defaulting to `{defaults.STATE_KEY_NAME}`"
            warnings.warn(_msg)
        else:
            if not settings.STATE_KEY_NAME:
                _msg = f"STATE_KEY_NAME setting is set to `{settings.STATE_KEY_NAME}` which is logically incorrect."
                info=Info(
                    _msg
                )
                errors.append(info)

        if not hasattr(settings, "FINAL_REDIRECT_KEY_NAME"):
            setattr(settings, "FINAL_REDIRECT_KEY_NAME", defaults.FINAL_REDIRECT_KEY_NAME)
            _msg = f"FINAL_REDIRECT_KEY_NAME settings is not defined. Defaulting to `{defaults.FINAL_REDIRECT_KEY_NAME}`"
            warnings.warn(_msg)
        else:
            if not settings.FINAL_REDIRECT_KEY_NAME:
                _msg = f"FINAL_REDIRECT_KEY_NAME setting is set to `{settings.FINAL_REDIRECT_KEY_NAME}` which is logically incorrect."
                info=Info(
                    _msg
                )
                errors.append(info)
        return errors 