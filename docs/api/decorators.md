---
title: Decorators API
description: API reference for Django Gauth view-protection helpers.
tags:
  - api
  - decorators
  - user-integration
---

# Decorators API :material-shield-lock:

View-protection helpers, exported from the package root:

```python
from django_gauth import gauth_required, GauthRequiredMixin
```

Both are **dual-mode**: when
[`GOOGLE_USER_INTEGRATION`](../configuration/settings.md#google_user_integration) is
enabled they read `request.user.is_authenticated` (so admin/password logins count too);
otherwise they fall back to the session-only
[`check_gauth_authentication()`](utilities.md#check_gauth_authenticationsession) check —
so they work with or without a `User` model.

On failure they honour the same `response=` convention as `login()` / `logout()`:
`redirect` (a `302` to the login endpoint, default) or `json` (a `401` body).

---

## `gauth_required`

Protects a **function-based view**. Usable bare or parameterised.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `view_func` | `Callable \| None` | — | Supplied automatically when used bare |
| `response` | `str` | `"redirect"` | `"redirect"` (302 to login) or `"json"` (401 body) |
| `login_url` | `str \| None` | `None` | Redirect target override; defaults to `reverse("django_gauth:login")` |

**Raises:** `ValueError` if `response` is not `"redirect"` or `"json"`.

```python
from django_gauth import gauth_required

@gauth_required
def dashboard(request):
    return render(request, "dashboard.html")

@gauth_required(response="json")
def api_me(request):
    return JsonResponse({"email": request.user.email})

@gauth_required(login_url="/accounts/login/")
def billing(request):
    ...
```

On an unauthenticated request the `json` mode returns:

```json
{ "detail": "Authentication required.", "authenticated": false }
```

---

## `GauthRequiredMixin`

The class-based-view equivalent. Place it **before** the base view so `super().dispatch`
resolves correctly, and configure via class attributes.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `gauth_response` | `str` | `"redirect"` | `"redirect"` or `"json"` |
| `gauth_login_url` | `str \| None` | `None` | Redirect target override |

**Raises:** `ValueError` (at dispatch) if `gauth_response` is invalid.

```python
from django.views.generic import TemplateView
from django_gauth import GauthRequiredMixin

class Dashboard(GauthRequiredMixin, TemplateView):
    template_name = "dashboard.html"

class MeView(GauthRequiredMixin, View):
    gauth_response = "json"

    def get(self, request):
        return JsonResponse({"email": request.user.email})
```

!!! tip "Works before you have a User model"
    Because the guard falls back to the session check when integration is off, you can
    protect views on day one — and the **same** decorator keeps working unchanged once you
    flip on `GOOGLE_USER_INTEGRATION`.
