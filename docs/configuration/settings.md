---
title: Settings Reference
description: Complete reference of all Django Gauth settings.
tags:
  - configuration
  - settings
---

# Settings Reference :material-cog:

All settings are defined in your Django project's `settings.py`.

---

## Required Settings

!!! danger "These must be set or your app won't start"

### `GOOGLE_CLIENT_ID`

:   Your Google OAuth2 client identifier.

    ```python
    GOOGLE_CLIENT_ID = "123456789-abc.apps.googleusercontent.com"
    ```

    **Type:** `str` · **Default:** None (required)

### `GOOGLE_CLIENT_SECRET`

:   Your Google OAuth2 client secret.

    ```python
    GOOGLE_CLIENT_SECRET = "GOCSPX-xxxxxxxxxxxxxxxx"
    ```

    **Type:** `str` · **Default:** None (required)

---

## Optional Settings

### `SCOPE`

:   List of OAuth2 scopes defining what access your app requests.

    ```python
    SCOPE = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]
    ```

    **Type:** `list[str]` · **Default:** `[]` (with warning)

    !!! tip "Common Scopes"
        | Scope | What it grants |
        |-------|---------------|
        | `openid` | Basic identity (required for ID token) |
        | `.../userinfo.email` | User's email |
        | `.../userinfo.profile` | Name, picture, locale |
        | `.../drive` | Full Google Drive access |
        | `.../drive.readonly` | Read-only Drive access |
        | `.../calendar` | Google Calendar |

### `GOOGLE_AUTH_FINAL_REDIRECT_URL`

:   Where to redirect after successful authentication.

    ```python
    # Redirect to your app's dashboard
    GOOGLE_AUTH_FINAL_REDIRECT_URL = "/dashboard/"

    # Or use None to go back to /gauth/ landing page
    GOOGLE_AUTH_FINAL_REDIRECT_URL = None
    ```

    **Type:** `Optional[str]` · **Default:** `None` (redirects to `/gauth/`)

### `CREDENTIALS_SESSION_KEY_NAME`

:   The session key where OAuth2 credentials are stored.

    ```python
    CREDENTIALS_SESSION_KEY_NAME = "credentials"
    ```

    **Type:** `str` · **Default:** `"credentials"`

### `STATE_KEY_NAME`

:   The session key where the OAuth2 state parameter is stored.

    ```python
    STATE_KEY_NAME = "oauth_state"
    ```

    **Type:** `str` · **Default:** `"oauth_state"`

### `DJANGO_GAUTH_UI_CONFIG`

:   Customize the appearance of the built-in landing page.

    ```python
    DJANGO_GAUTH_UI_CONFIG = {
        "index": {
            "navbar": {
                "logo": "https://example.com/my-logo.png",
                "profile_picture_absence": "https://example.com/placeholder.png",
            }
        }
    }
    ```

    **Type:** `dict` · **Default:** Not set (uses built-in assets)

    See [UI Customization](ui-customization.md) for details.

---

## Environment Variable

### `OAUTHLIB_INSECURE_TRANSPORT`

:   Allows OAuth2 over HTTP (non-HTTPS). **Development only!**

    ```python
    import os
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # ⚠️ DEV ONLY
    ```

    !!! danger "Never enable in production"
        This disables HTTPS requirement. In production, always use HTTPS.

---

## Settings Summary Table

| Setting | Required | Type | Default |
|---------|:--------:|------|---------|
| `GOOGLE_CLIENT_ID` | ✅ | `str` | — |
| `GOOGLE_CLIENT_SECRET` | ✅ | `str` | — |
| `SCOPE` | ⚠️ | `list` | `[]` |
| `GOOGLE_AUTH_FINAL_REDIRECT_URL` | ❌ | `str\|None` | `None` |
| `CREDENTIALS_SESSION_KEY_NAME` | ❌ | `str` | `"credentials"` |
| `STATE_KEY_NAME` | ❌ | `str` | `"oauth_state"` |
| `DJANGO_GAUTH_UI_CONFIG` | ❌ | `dict` | Not set |

---

## System Checks

Django Gauth validates your settings when the server starts:

| Code | Level | Message |
|------|-------|---------|
| `django_gauth.E001` | Error | `SECRET_KEY` not defined |
| `django_gauth.E002` | Error | `SessionMiddleware` not in `MIDDLEWARE` |
| `django_gauth.E003` | Error | `GOOGLE_CLIENT_ID` or `GOOGLE_CLIENT_SECRET` missing |
| `django_gauth.E004` | Warning | `SCOPE` not defined |

Run checks manually:

```bash
python manage.py check
```
