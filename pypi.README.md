# Google Auth <sup>[ Django ]</sup>

[![PyPI version](https://img.shields.io/pypi/v/django-gauth?label=PyPI&color=blue)](https://pypi.org/project/django-gauth/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-gauth)](https://pypi.org/project/django-gauth/)
[![Django versions](https://img.shields.io/pypi/frameworkversions/django/django-gauth?label=Django&color=0C4B33)](https://pypi.org/project/django-gauth/)
[![Downloads](https://img.shields.io/pypi/dm/django-gauth?label=downloads&color=brightgreen)](https://pypi.org/project/django-gauth/)
[![License](https://img.shields.io/pypi/l/django-gauth?color=green)](https://github.com/masterPiece93/django-gauth/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-online-blue)](https://masterpiece93.github.io/django-gauth/)
[![pages-build-deployment](https://github.com/masterPiece93/django-gauth/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/masterPiece93/django-gauth/actions/workflows/pages/pages-build-deployment)
[![Pylint](https://github.com/masterPiece93/django-gauth/actions/workflows/pylint.yml/badge.svg)](https://github.com/masterPiece93/django-gauth/actions/workflows/pylint.yml)

> [Official Documentation](https://masterpiece93.github.io/django-gauth/)

## Why django-gauth?

> **Google sign-in for Django in 5 minutes — without the django-allauth configuration maze.**

`django-gauth` does exactly one thing well: add **Google OAuth2 login** to an HTTP/HTTPS Django
project, with a working landing page included — no multi-provider abstractions, no sprawling
configuration, just the Google flow, clearly documented.

| | **django-gauth** | **django-allauth** | **Roll-your-own** |
| --- | :---: | :---: | :---: |
| Setup for *just Google* | ⚡ Minimal (3 settings + 1 URL include) | 🧩 Broad, multi-step config | 🛠️ Manual OAuth wiring |
| Built-in login page | ✅ Ships a landing page | ➖ Bring your own templates | ❌ Build it yourself |
| Scope | 🎯 Google OAuth2 only | 🌐 Many providers | 🎯 Whatever you build |
| Learning curve | 📉 Low | 📈 Higher (large surface) | ⚠️ Easy to get OAuth subtly wrong |
| Typed & tested | ✅ Type hints + ~99% coverage | ✅ Mature | ➖ Up to you |

**Reach for `django-allauth`** when you need many providers, account linking, and email
workflows. **Reach for `django-gauth`** when you want Google sign-in working *today* with
minimal ceremony.

## Installation

<!-- Implement Carousal -->

| Source | Command |
| ------ | ------- |
| **GitHub** | ```pip install -e git+https://github.com/masterPiece93/django-gauth.git#egg=django_gauth```|
| **PyPi**| ```pip install django-gauth``` |

## Quickstart

1. add the app name : `django_gauth` in **INSTALLED_APPS** entry of you project ( in settings.py file )
2. add required configuration variables ( in *settings.py* file )    
    ```python
    # settings.py
    GOOGLE_CLIENT_ID= env("GOOGLE_CLIENT_ID")           # << set according to your oauth2 client
    GOOGLE_CLIENT_SECRET= env("GOOGLE_CLIENT_SECRET")   # << set according to your oauth2 client
    GOOGLE_AUTH_FINAL_REDIRECT_URL= None        # defaults to `<host>/gauth/`
    CREDENTIALS_SESSION_KEY_NAME= "credentials" # defaults to `credentials`
    STATE_KEY_NAME= "oauth_state"               # defaults to `oauth_state`
    SCOPE= [
        "https://www.googleapis.com/auth/userinfo.email"    # always preffered
        ,"https://www.googleapis.com/auth/userinfo.profile" # always preffered
        ,"openid"                                           # always preffered
        ,"https://www.googleapis.com/auth/drive"            # based on your usage
    ]
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'         # strictly for local-development only
    ```

    - `os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'` directs the server to accept in-secure (http) connections .

3. configure auth urls ( in *urls.py* file of root )
    ```python
    # urls.py
    from django.contrib import admin
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('gauth/', include('django_gauth.urls')),
        
        # add your other app's urls
        # ...

    ]
    ```
4. now run your project server
    - once your server is up & running , navigate to `.../gauth`, this is the master interface ( default landing page )
    - click on `Authenticate` button to launch Google Oauth2 Login .
    - just follow the flow you are directed to .
    - post authentication , you'll be redirected back to `.../gauth`

* NOTE : 
    useually all servers ( **wsgi**, **asgi**, **uWsgi**) runs default on `http://127.0.0.1:PORT/` , hence always take care to set the redirect endpoints in your google oauth2 client app in accordance with *127.0.0.1* , don't mistake to consider *localhost* , *0.0.0.0* and *127.0.0.1* as the same thing while dealing with redirect uri's . 
    - For example : suppose you have set `http://localhost:PORT/gauth/google-callback` as your redirect uri , then take note of running your django app on localhost:PORT only !!

---

## Changelog

See [`CHANGELOG.md`](https://github.com/masterPiece93/django-gauth/blob/main/CHANGELOG.md) for the full release history and notable changes in each version.

<br>

## Releases

See [`Github Releases`](https://github.com/masterPiece93/django-gauth/releases) for the details of each release in each version .

<br>

