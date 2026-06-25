---
title: Architecture
description: How Django Gauth is structured internally.
tags:
  - concepts
  - architecture
---

# Architecture :material-sitemap:

Understanding how Django Gauth is organized helps you extend and debug it.

---

## Package Structure

```mermaid
graph TD
    subgraph django_gauth["📦 django_gauth"]
        apps[apps.py<br/><small>App config & startup checks</small>]
        views[views.py<br/><small>HTTP endpoints</small>]
        urls[urls.py<br/><small>URL routing</small>]
        utilities[utilities.py<br/><small>Helper functions</small>]
        checks[_checks.py<br/><small>System check framework</small>]
        defaults[defaults.py<br/><small>Default configuration values</small>]
        admin[admin.py<br/><small>Admin panel integration</small>]
        templates[templates/<br/><small>HTML landing page</small>]
        static[static/<br/><small>CSS, images</small>]
    end

    apps --> checks
    apps --> defaults
    views --> utilities
    urls --> views

    style django_gauth fill:#f5f5f5,stroke:#333
```

---

## Component Responsibilities

### Views (`views.py`)

The core of the OAuth2 flow:

```mermaid
graph LR
    subgraph "Views"
        index["index()<br/>Landing page"]
        login["login()<br/>Start OAuth flow"]
        callback["callback()<br/>Handle Google response"]
        debug["debug_information()<br/>Debug JSON (DEBUG only)"]
    end

    index -->|"Authenticate btn"| login
    login -->|"Google redirects back"| callback
```

| View | Method | URL | Purpose |
|------|--------|-----|---------|
| `index` | GET | `/gauth/` | Render landing page with user info |
| `login` | GET | `/gauth/login/` | Build OAuth URL, redirect to Google |
| `callback` | GET | `/gauth/login-callback` | Exchange code, store tokens |
| `debug_information` | GET | `/gauth/debug` | Show session data (DEBUG only) |

### System Checks (`_checks.py` + `apps.py`)

Django Gauth validates your configuration at startup using Django's [System Check Framework](https://docs.djangoproject.com/en/stable/topics/checks/):

```mermaid
graph TD
    A[Django starts] --> B{django.setup}
    B --> C[DjangoGauthConfig.ready]
    C --> D[Register checks]
    D --> E[check_project_settings]
    D --> F[check_project_middlewares]
    D --> G[set_defaults]

    E --> |Missing?| H[❌ Error E001/E003]
    F --> |Missing?| I[❌ Error E002]
    G --> |Missing?| J[⚠️ Set defaults + warn]

    style H fill:#f44336,color:white
    style I fill:#f44336,color:white
    style J fill:#FF9800,color:white
```

| Check | Error Code | Validates |
|-------|------------|-----------|
| `check_project_settings` | E001 | `SECRET_KEY` exists |
| `check_project_settings` | E003 | `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET` exist |
| `check_project_middlewares` | E002 | `SessionMiddleware` is in `MIDDLEWARE` |
| `set_defaults` | E004 | `SCOPE` is defined |

### Utilities (`utilities.py`)

Pure helper functions with no side effects:

| Function | Purpose |
|----------|---------|
| `credentials_to_dict()` | Serialize Google credentials to dict for session storage |
| `has_epoch_time_passed()` | Check if a token has expired |
| `check_gauth_authentication()` | Verify if current session is authenticated |
| `is_valid_google_url()` | Validate Google Docs URLs |

### Defaults (`defaults.py`)

Defines fallback values when settings are not configured:

```python
GOOGLE_AUTH_FINAL_REDIRECT_URL = None    # → /gauth/
CREDENTIALS_SESSION_KEY_NAME = "credentials"
STATE_KEY_NAME = "oauth_state"
FINAL_REDIRECT_KEY_NAME = "final_redirect"
```

---

## Request Lifecycle

Here's what happens for each HTTP request through Django Gauth:

```mermaid
flowchart TD
    A[HTTP Request] --> B{URL Match?}
    B -->|/gauth/| C[index view]
    B -->|/gauth/login/| D[login view]
    B -->|/gauth/login-callback| E[callback view]
    B -->|/gauth/debug| F{DEBUG=True?}
    F -->|Yes| G[debug_information view]
    F -->|No| H[404]

    C --> C1[check_gauth_authentication]
    C1 --> C2[Render template with context]

    D --> D1[get_origin_url]
    D1 --> D2[Create OAuth Flow]
    D2 --> D3[Generate authorization URL]
    D3 --> D4[Store state in session]
    D4 --> D5[302 Redirect to Google]

    E --> E1[Retrieve state from session]
    E1 --> E2[Create OAuth Flow with state]
    E2 --> E3[Exchange code for tokens]
    E3 --> E4[Verify ID token]
    E4 --> E5[Store credentials in session]
    E5 --> E6[302 Redirect to final URL]

    style D5 fill:#2196F3,color:white
    style E6 fill:#4CAF50,color:white
```

---

## Session Data Model

After successful authentication, Django Gauth stores this in the session:

```mermaid
classDiagram
    class Session {
        +dict credentials
        +dict id_info
        +str oauth_state
        +str final_redirect
        +dict debug (DEBUG only)
    }

    class Credentials {
        +str token
        +str refresh_token
        +str token_uri
        +str client_id
        +str client_secret
        +list scopes
    }

    class IdInfo {
        +str email
        +str name
        +str picture
        +bool email_verified
        +int exp
    }

    Session --> Credentials
    Session --> IdInfo
```

---

## Integration Points

```mermaid
graph TD
    subgraph "Your Django Project"
        S[settings.py]
        U[urls.py]
        V[Your Views]
    end

    subgraph "django_gauth"
        GA[django_gauth app]
    end

    subgraph "External"
        G[Google OAuth2]
        GS[Google APIs]
    end

    S -->|"GOOGLE_CLIENT_ID<br/>GOOGLE_CLIENT_SECRET<br/>SCOPE"| GA
    U -->|"include('django_gauth.urls')"| GA
    GA <-->|"OAuth2 flow"| G
    V -->|"Read session['credentials']"| GA
    V -->|"Use access_token"| GS
```

!!! tip "Accessing credentials in your views"
    After authentication, you can access the stored credentials:

    ```python
    def my_view(request):
        credentials = request.session.get("credentials")
        if credentials:
            # User is authenticated!
            access_token = credentials["token"]
            # Use access_token to call Google APIs
    ```
