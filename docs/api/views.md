---
title: Views API
description: API reference for Django Gauth view functions.
tags:
  - api
  - views
---

# Views API :material-api:

All views are in `django_gauth.views`.

---

## `index(request)`

Renders the Django Gauth landing page.

| Property | Value |
|----------|-------|
| **URL** | `/gauth/` |
| **Method** | `GET` |
| **URL Name** | `django_gauth:index` |
| **Template** | `django_gauth/index.html` |

**Context data passed to template:**

| Key | Type | Description |
|-----|------|-------------|
| `is_authenticated` | `bool` | Whether user has valid credentials |
| `login_href` | `str` | URL to the login endpoint |
| `user_info` | `dict` | User's id_info (email, name, picture) |
| `index` | `dict` | UI config (if `DJANGO_GAUTH_UI_CONFIG` set) |

---

## `login(request)`

Initiates the Google OAuth2 flow.

| Property | Value |
|----------|-------|
| **URL** | `/gauth/login/` |
| **Method** | `GET` |
| **URL Name** | `django_gauth:login` |
| **Response** | `302 Redirect` to Google |

**Query Parameters:**

| Param | Optional | Description |
|-------|:--------:|-------------|
| `origin_url` | ✅ | URL to redirect to after auth (same-origin only) |

**What it does:**

```mermaid
flowchart LR
    A[Validate origin_url] --> B[Create OAuth Flow]
    B --> C[Generate auth URL + state]
    C --> D[Store state in session]
    D --> E[302 → Google]
```

---

## `callback(request)`

Handles Google's OAuth2 callback after user consent.

| Property | Value |
|----------|-------|
| **URL** | `/gauth/login-callback` |
| **Method** | `GET` |
| **URL Name** | `django_gauth:callback` |
| **Response** | `302 Redirect` to final URL |

**Query Parameters (set by Google):**

| Param | Description |
|-------|-------------|
| `code` | Authorization code to exchange for tokens |
| `state` | State parameter for CSRF verification |

**What it does:**

```mermaid
flowchart LR
    A[Verify state] --> B[Exchange code for tokens]
    B --> C[Verify ID token]
    C --> D[Store credentials in session]
    D --> E[302 → final redirect]
```

---

## `debug_information(request)`

Returns sanitized session data as JSON. **Only available when `DEBUG=True`.**

| Property | Value |
|----------|-------|
| **URL** | `/gauth/debug` |
| **Method** | `GET` |
| **URL Name** | `django_gauth:debug` |
| **Response** | `JsonResponse` |

**Sanitization:**

- `id_info`: Removes `iss`, `azp`, `aud`, `sub`
- `credentials`: Shows existence only (not raw tokens)
- `oauth_state`: Completely removed

---

## `get_origin_url(request)`

Internal helper — validates and extracts the `origin_url` query parameter.

| Property | Value |
|----------|-------|
| **Returns** | `tuple[Optional[str], bool]` |
| **First element** | The decoded origin URL (or `None`) |
| **Second element** | Whether it's a valid same-origin URL |

!!! info "Same-origin validation"
    Only URLs with matching `scheme` and `netloc` are considered valid.
