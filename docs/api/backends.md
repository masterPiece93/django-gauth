---
title: Backends API
description: API reference for the Django Gauth authentication backend.
tags:
  - api
  - backends
  - user-integration
---

# Backends API :material-account-key:

The backend lives in `django_gauth.backends` and powers the optional
[Django User Integration](../concepts/django-user-integration.md). It is inert unless you
enable `GOOGLE_USER_INTEGRATION` **and** register it in `AUTHENTICATION_BACKENDS`.

```python
AUTHENTICATION_BACKENDS = [
    "django_gauth.backends.GoogleAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

---

## `GoogleAuthBackend`

A Django authentication backend (subclass of
`django.contrib.auth.backends.BaseBackend`) that turns a **verified** Google `id_info`
into a row in your existing `AUTH_USER_MODEL`. It stores **no tokens** and adds **no
models** — identity mapping only.

### `authenticate(request, id_info=None, **kwargs)`

Resolves a Google identity to a user.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `request` | `HttpRequest` | The current request (unused, kept for the backend contract) |
| `id_info` | `dict \| None` | The verified ID-token claims. **When `None`, the backend opts out** and returns `None` |

**Returns:** `Optional[User]` — the mapped user, or `None`.

The backend is **passive**: with no `id_info` it returns `None` immediately, so a
username/password `authenticate()` call falls through to `ModelBackend`. When `id_info` is
supplied it delegates to
[`get_or_create_user_from_id_info()`](utilities.md#get_or_create_user_from_id_infoid_info)
and additionally returns `None` for an **inactive** user (`is_active is False`).

```python
from django.contrib.auth import authenticate

user = authenticate(request, id_info=verified_claims)
# → the matched/created User, or None if refused
```

### `get_user(user_id)`

Standard session-restore hook: loads a user by primary key.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `user_id` | `Any` | The primary key stored in the session |

**Returns:** `Optional[User]` — the user, or `None` if the pk no longer exists.

!!! info "Keep `ModelBackend` too"
    Registering `GoogleAuthBackend` **alongside** `ModelBackend` is the supported setup —
    Google sign-in and password/admin login then coexist. `manage.py check` warns
    (`django_gauth.W003`) if the backend is missing while integration is on.
