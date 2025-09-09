# Google Auth <sup>[ Django ]<sup>

## Developer Zone

> [Developer README](./dev.README.md)

### Important Points

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
