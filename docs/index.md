---
title: Django Gauth — Google OAuth2 for Django
description: Add Google Sign-In to your Django project in minutes.
tags:
  - home
  - overview
---

# Django Gauth :material-google: :material-shield-lock:

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } **Set up in 5 minutes**

    ---

    Install with `pip`, add 3 settings, include one URL — done.

    [:octicons-arrow-right-24: Quickstart](quickstart.md)

-   :material-security:{ .lg .middle } **Production Ready**

    ---

    Built on Google's official `google-auth-oauthlib` library with session-based security.

    [:octicons-arrow-right-24: Production Guide](guides/production.md)

-   :material-puzzle:{ .lg .middle } **Django Native**

    ---

    Works with Django 3.1 → 5.2, Python 3.9 → 3.12. Uses standard Django sessions.

    [:octicons-arrow-right-24: Configuration](configuration/settings.md)

-   :material-palette:{ .lg .middle } **Customizable UI**

    ---

    Override logos, colors, and redirect behavior via simple settings.

    [:octicons-arrow-right-24: UI Customization](configuration/ui-customization.md)

-   :material-transit-connection-variant:{ .lg .middle } **Nested & Dynamic Auth**

    ---

    Sign users in from *anywhere* in your app and send them **right back to where
    they started** — in the same state. Origin-preserving redirection, built in.

    [:octicons-arrow-right-24: Redirection Schemes](concepts/redirection-schemes.md)

-   :material-refresh-auto:{ .lg .middle } **Session Lifecycle**

    ---

    Sessions **survive past Google's 1-hour token expiry** via transparent refresh,
    and a clean `logout()` that **revokes the Google token** — not just the local
    session.

    [:octicons-arrow-right-24: Session Lifecycle](concepts/session-lifecycle.md)

</div>

---

## What is Django Gauth?

**Django Gauth** is a plug-and-play Django app that adds Google OAuth2 authentication to any Django project. It handles the entire OAuth2 flow — from redirecting users to Google's consent screen to storing credentials in Django sessions.

```mermaid
graph LR
    A[Your Django App] -->|pip install| B[django_gauth]
    B --> C[Google OAuth2]
    C --> D[User Authenticated ✓]
    D --> A
```

## Why Use This?

| Feature | Django Gauth | DIY OAuth2 |
|---------|:------------:|:----------:|
| Setup time | ~5 min | ~2 days |
| Built-in landing page | :white_check_mark: | :x: |
| Session management | :white_check_mark: | Manual |
| Nested & dynamic auth (return-to-origin) | :white_check_mark: | Manual & error-prone |
| Session refresh + revoking logout | :white_check_mark: | Manual & error-prone |
| System checks on startup | :white_check_mark: | :x: |
| Debug endpoint | :white_check_mark: | :x: |
| Type hints | :white_check_mark: | Varies |

## How is this different from allauth / social-auth?

[django-allauth](https://docs.allauth.org/) and
[python-social-auth](https://python-social-auth.readthedocs.io/) are excellent,
full-featured **authentication frameworks**. Django Gauth isn't competing with
them on breadth — it deliberately fills a **narrower niche**, and the difference
is **architectural, not mechanical**.

Both frameworks bind to Django's `User` model and persist accounts and tokens in
the **database** (their own models + migrations) — that's what gives you real
user accounts, multiple providers, admin integration, email/password, and
account linking. Django Gauth keeps Google identity in the **session only**:
**no `User` model, no migrations, no ORM token store.**

| | Django Gauth | allauth / social-auth |
|---|:---:|:---:|
| Requires a Django `User` | :x: session-only | :white_check_mark: |
| DB models + migrations | :x: none | :white_check_mark: |
| Providers | Google only | Many |
| Account management (signup, email, linking) | :x: | :white_check_mark: |
| Footprint | one small app | full framework |

!!! tip "Which should you pick?"
    - **Choose allauth or social-auth** if you want real user *accounts* — a
      `User` row per person, multiple providers, email/password, account linking,
      or Django-admin integration.
    - **Choose Django Gauth** if you just need to answer *"is this request a
      signed-in Google user?"* for an **SPA or API backend** — delivered as a JSON
      [`/gauth/session`](api/views.md#session_statusrequest) probe with a
      configurable [session policy](concepts/session-lifecycle.md#choosing-a-session-policy),
      **without** adopting an auth framework, a `User` table, or migrations.

!!! note "On refresh & SPA support — being fair"
    Neither transparent refresh nor SPA support is unique: social-auth ships a
    token-refresh helper, and allauth offers a Headless API for frontends. Django
    Gauth's contribution is delivering session refresh, a JSON auth probe,
    configurable session caps, and revoking logout in that **stateless,
    `User`-model-free** setting — where you'd otherwise wire it by hand.

## Compatibility

| Python | Django |
|--------|--------|
| 3.9, 3.10, 3.11, 3.12 | 3.1, 3.2, 4.0, 4.1, 4.2, 5.0, 5.1, 5.2 |

## Quick Install

```bash
pip install django-gauth
```

[:material-rocket-launch: Get Started →](quickstart.md){ .md-button .md-button--primary }
[:material-book-open-variant: Read the Concepts →](concepts/oauth2-explained.md){ .md-button }
