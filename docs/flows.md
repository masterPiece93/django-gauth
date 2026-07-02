---
title: Authentication Flows
description: Visual diagrams of all authentication flows in Django Gauth.
tags:
  - flows
  - diagrams
---

# Authentication Flows :material-transit-connection-variant:

This page provides detailed visual representations of every flow in Django Gauth.

---

## High-Level Browser Flow

What the **user** experiences:

```mermaid
graph LR
    A["/gauth/"] --> B[Landing Screen]
    B --> |"Click Authenticate"| C[Google Account Selection]
    C --> D{Already signed in?}
    D --> |Yes| E[Google Consent Screen]
    D --> |No| F[Enter Google Password]
    F --> E
    E --> G{User consents?}
    G --> |Yes| H[✅ Authenticated!]
    H --> B
    G --> |No| I[❌ Access Denied]

    style H fill:#4CAF50,color:white
    style I fill:#f44336,color:white
```

---

## Complete HTTP Sequence Flow

What happens at the **network level**:

```mermaid
sequenceDiagram
    autonumber
    participant B as 🌐 Browser
    participant D as 🖥️ Django Server
    participant G as 🔐 Google OAuth2
    participant API as 📦 Google Token API

    B->>D: GET /gauth/
    D-->>B: 200 HTML (Landing Page)

    Note over B,G: User clicks "Authenticate"

    B->>D: GET /gauth/login/
    D->>D: Create Flow object
    D->>D: Generate state, store in session
    D-->>B: 302 → accounts.google.com/o/oauth2/v2/auth

    B->>G: GET /o/oauth2/v2/auth?client_id=...&state=...
    G-->>B: 200 Account Picker / Consent

    Note over B,G: User selects account & consents

    G-->>B: 302 → /gauth/login-callback?code=AUTH_CODE&state=STATE

    B->>D: GET /gauth/login-callback?code=...&state=...
    D->>D: Verify state from session
    D->>API: POST /token {code, client_id, client_secret}
    API-->>D: {access_token, id_token, refresh_token}
    D->>D: Verify id_token (signature + claims)
    D->>D: Store credentials & user info in session
    D-->>B: 302 → Final Redirect URL

    B->>D: GET /gauth/ (or custom URL)
    D-->>B: 200 HTML (Authenticated view)
```

---

## Login with Origin URL Flow

When your app passes `origin_url` for post-auth redirection:

```mermaid
sequenceDiagram
    participant App as 🖥️ Your App Page
    participant D as Django Gauth
    participant G as Google

    App->>D: GET /gauth/login/?origin_url=http://yourapp/dashboard/
    D->>D: Validate origin_url (same-origin check)

    alt origin_url is valid (same origin)
        D->>D: Store origin_url as final redirect
    else origin_url is invalid (cross-origin)
        D->>D: Use default GOOGLE_AUTH_FINAL_REDIRECT_URL
    end

    D-->>G: Redirect to Google
    G-->>D: Callback with tokens
    D-->>App: Redirect to stored final URL
```

---

## Session State Transitions

How the Django session evolves throughout the flow:

```mermaid
stateDiagram-v2
    [*] --> Empty: New session

    Empty --> HasState: GET /gauth/login/
    note right of HasState
        session = {
            oauth_state: "abc123",
            final_redirect: "/dashboard/"
        }
    end note

    HasState --> Authenticated: GET /gauth/login-callback
    note right of Authenticated
        session = {
            oauth_state: "abc123",
            final_redirect: "/dashboard/",
            credentials: {token, refresh_token, ...},
            id_info: {email, name, picture, exp}
        }
    end note

    Authenticated --> Expired: id_info.exp passes
    Expired --> HasState: Re-authenticate
```

---

## Token Lifecycle

```mermaid
gantt
    title Token Lifetimes
    dateFormat X
    axisFormat %s

    section Authorization Code
    Code valid           :0, 600

    section Access Token
    Token valid          :0, 3600

    section Refresh Token
    Refresh valid        :0, 31536000

    section ID Token
    ID Token valid       :0, 3600
```

| Token | Typical Lifetime | Can be refreshed? |
|-------|:----------------:|:-----------------:|
| Authorization Code | ~10 min | No (one-time use) |
| Access Token | ~1 hour | Yes (with refresh token) |
| Refresh Token | ~1 year | No (new one issued) |
| ID Token | ~1 hour | Yes (with refresh token) |

---

## Session Refresh Flow

How the `/gauth/session` probe survives the ~1 hour ID-token expiry by
transparently refreshing. See [Session Lifecycle](concepts/session-lifecycle.md).

```mermaid
sequenceDiagram
    autonumber
    participant B as 🌐 SPA / Browser
    participant D as 🖥️ Django Server
    participant G as 🔐 Google Token API

    B->>D: GET /gauth/session
    D->>D: check_gauth_authentication(session)

    alt Session still valid
        D-->>B: 200 { authenticated: true, user }
    else id_info expired, refresh_token present
        D->>G: POST /token (grant_type=refresh_token)
        G-->>D: fresh access_token + id_token
        D->>D: Re-verify fresh id_token → new id_info
        D->>D: Write credentials + id_info back to session
        D-->>B: 200 { authenticated: true, user }
    else No refresh possible
        D-->>B: 200 { authenticated: false, user: null }
    end
```

---

## Logout Flow

`/gauth/logout/` clears the session and best-effort revokes the Google token.

```mermaid
sequenceDiagram
    autonumber
    participant B as 🌐 Browser / SPA
    participant D as 🖥️ Django Server
    participant G as 🔐 Google Revoke API

    B->>D: GET /gauth/logout/  (?response=redirect|json)

    opt GOOGLE_TOKEN_REVOKE_ON_LOGOUT and token in session
        D->>G: POST /revoke (refresh_token)
        G-->>D: 200 (best-effort — failures ignored)
    end

    D->>D: session.flush() — rotates the session key

    alt response=json
        D-->>B: 200 { status: logged_out }
    else response=redirect (default)
        D-->>B: 302 → GOOGLE_AUTH_LOGOUT_REDIRECT_URL (or /gauth/)
    end
```

---

## Error Flows

### Redirect URI Mismatch

```mermaid
sequenceDiagram
    participant B as Browser
    participant D as Django
    participant G as Google

    B->>D: GET /gauth/login/
    D-->>B: 302 → Google (redirect_uri=http://127.0.0.1:8000/gauth/login-callback)
    B->>G: GET /auth?redirect_uri=http://127.0.0.1:8000/gauth/login-callback
    G-->>B: ❌ Error 400: redirect_uri_mismatch

    Note over B,G: Google's registered URI doesn't match!
```

### User Denies Consent

```mermaid
sequenceDiagram
    participant B as Browser
    participant D as Django
    participant G as Google

    B->>D: GET /gauth/login/
    D-->>B: 302 → Google
    B->>G: User clicks "Deny"
    G-->>B: 302 → /gauth/login-callback?error=access_denied
    B->>D: GET /gauth/login-callback?error=access_denied
    D-->>B: 302 → final redirect (graceful, no crash)
```

### State Mismatch (CSRF / expired / replayed link)

```mermaid
sequenceDiagram
    participant B as Browser
    participant D as Django

    B->>D: GET /gauth/login-callback?state=WRONG&code=...
    D->>D: Compare state vs session
    D-->>B: ❌ 400 Bad Request — "Invalid or missing OAuth state"

    Note over B,D: Restart sign-in from /gauth/login/
```