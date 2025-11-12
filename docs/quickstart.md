## Steps To Follow 

:fontawesome-brands-square-kickstarter: a real quick starter !! :beers:

1. Add the app name - `django_gauth` in INSTALLED_APPS entry of you project 
    - <em><small>in your django project's settings.py file</small></em> :
    ```py title="settings.py" linenums="1" hl_lines="8"
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django_gauth',
    ]
    ```
2. Add required configuration variables 
    - <em><small>in your django project's root ( location : `project-name/project-name/` )</small></em> :
    ```py title="settings.py" linenums="1"

    ... # ... rest of your settings.py file content

    # --- END OF FILE :

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
    - explainantion :
        - `os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'` directs the server to accept in-secure ( http ) connections .

3. configure auth urls 
    - <em><small>in your django project's root ( location : `project-name/project-name/` )</small></em> :
    ```py title="urls.py" linenums="1" hl_lines="6"
    from django.contrib import admin
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('gauth/', include('django_gauth.urls')),
        
        # add your other app's urls
        # ...

    ]
    ```

- Now run the application server :

    === "127.0.0.1 ( default )"
        ```bnf
        python3 manage.py runserver 8000
        ```
    === "Localhost"
        ```bnf
        python3 manage.py runserver localhost:8000
        ```
    - > we have shown port 8000 in use, you can replace any port number of your choice in place of 8000 . ( e.g : 5000, 8080 etc ... )

Quick Use :

- once your server is up & running , navigate to `.../gauth`, this is the master interface ( default landing page )
- click on `Authenticate` button to launch Google Oauth2 Login .
- just follow the flow you are directed to .
- post authentication , you'll be redirected back to `.../gauth`

## Important Points

- useually all servers ( wsgi, asgi, uWsgi) runs default on `http://127.0.0.1:PORT/` , hence always take care to set the redirect endpoints in your google oauth2 client app in accordance with 127.0.0.1 , don't mistake to consider - _localhost_ , _0.0.0.0_ and _127.0.0.1_ as same while dealing with redirect uri's . 
    - **For example** : suppose you have set `http://localhost:PORT/gauth/google-callback` as your redirect uri , then take note of running your django app on localhost only !!
