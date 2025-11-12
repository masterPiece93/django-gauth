# Google Auth <sup>[ Django ]<sup>

![Static Badge](https://img.shields.io/badge/latest-0.1.2-blue)  [![pages-build-deployment](https://github.com/masterPiece93/django-gauth/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/masterPiece93/django-gauth/actions/workflows/pages/pages-build-deployment)  [![Pylint](https://github.com/masterPiece93/django-gauth/actions/workflows/pylint.yml/badge.svg)](https://github.com/masterPiece93/django-gauth/actions/workflows/pylint.yml) [![Upload Python Package](https://github.com/masterPiece93/django-gauth/actions/workflows/release.yml/badge.svg)](https://github.com/masterPiece93/django-gauth/actions/workflows/release.yml)


* [Official Documentation](https://masterpiece93.github.io/django-gauth/)

## Developer Zone

> [Developer README](./dev.README.md)

## Installation

<!-- Implement Carousal -->

from GitHub :
```sh
# Editable Installation (for Development)
pip install -e git+https://github.com/xavient/django-gauth.git#egg=django_gauth
```

```sh
# Main Branch (Latest Version)
pip install git+https://github.com/xavient/django-gauth.git
```

from PyPi
```sh
pip install django-gauth
```

from test PyPi
```sh
pip install -i https://test.pypi.org/simple/ django-gauth
```

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
    - post authetication , you'll be redirected back to `.../gauth`

> NOTE : usually all servers ( wsgi, asgi, uWsgi) runs default on `http://127.0.0.1:PORT/` , hence always take care to set the redirect endpoints in your google oauth2 client app in accordance with 127.0.0.1 , don't mistake to consider localhost , 0.0.0.0 and 127.0.0.1 as same while dealing with redirect uri's . For example : suppose you have set `http://localhost:PORT/gauth/google-callback` as your redirect uri , then take note of running your django app on localhost only !!

> NOTE : 
---
<br>

### Important Points <sup> <small>To Be Noted</small> </sup>

for production applications , that are working on http**s** , must ensure the following settings for django to be http**s** aware :
```sh
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

Your reverse proxy should add the X-Forwarded-Proto: https header to requests forwarded to Django.
Configure your reverse proxy to set X-Forwarded-Proto header ( Nginx Example ):
```sh
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    # ... SSL configuration ...

    location / {
        proxy_pass http://your_django_app_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https; # Crucial line
    }
}
```
