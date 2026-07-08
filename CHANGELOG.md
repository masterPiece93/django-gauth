# Changelog

All notable changes to **django-gauth** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
  Maintainer note: add new entries under "Unreleased" as you merge changes.
  On release, rename the section to the version + date and start a fresh
  "Unreleased" block. Keep the comparison links at the bottom in sync.
-->

## [Unreleased]

## [0.3.0] - 2026-07-09

### Security

- `oauth_state` (OAuth2 CSRF nonce) is now explicitly removed from the session on the
  success path of `callback()`. It is a single-use token — once `fetch_token()` completes
  it has no further purpose, and clearing it prevents stale CSRF material from lingering
  in the authenticated session. Error paths (`400` state-mismatch, `access_denied` redirect)
  intentionally retain it to allow the user to retry.

### Documentation

- Added a compatibility warning (installation, troubleshooting, README, and PyPI readme)
  advising users on `django-gauth < 0.2.1` to pin `google-auth-oauthlib<1.3.0,>=1.0.0`
  to avoid PKCE-related OAuth failures (issue #54).

### Added

- **Django User Integration (issue #85)** — an opt-in bridge from the session-only Google
  flow to Django's own auth system, so `request.user`, `@login_required`, and the admin
  recognise Google-authenticated visitors — **with no `django-gauth` models and zero
  migrations**. Off by default; enable with `GOOGLE_USER_INTEGRATION = True` and register
  the backend.
    - **`GoogleAuthBackend`** (`django_gauth.backends`) — a passive
      `authenticate(request, id_info=...)` backend that maps a verified `id_info` to your
      existing `AUTH_USER_MODEL` and returns `None` for password logins, so
      `ModelBackend` keeps working alongside it.
    - **`get_or_create_user_from_id_info(id_info)`** (`django_gauth.utilities`) —
      model-free get-or-create keyed on a configurable lookup field (default `email`,
      case-insensitive), hard-gated by verified email.
    - **View seams** — `callback()` opens a Django auth session
      (`authenticate()` + `login()`) when integration is enabled; `logout()` also calls
      `auth.logout()`; and `session_status()` gains a top-level `user_id` (always present,
      `null` unless integrated **and** authenticated).
    - **`gauth_required` decorator** and **`GauthRequiredMixin`** (exported from
      `django_gauth`) — dual-mode view guards (`request.user` when integrated, otherwise
      the session-lifecycle check) that honour the `response=redirect|json` convention.
      Both routes enforce the session policy (`GOOGLE_SESSION_MAX_AGE` /
      `GOOGLE_SESSION_IDLE_TIMEOUT`), so a protected view blocks the moment a session
      exceeds a configured cap — consistent with the `/gauth/session` probe.
    - **Five new settings** — `GOOGLE_USER_INTEGRATION`, `GOOGLE_USER_AUTO_CREATE`,
      `GOOGLE_USER_LOOKUP_FIELD`, `GOOGLE_USER_REQUIRE_VERIFIED_EMAIL`, and
      `GOOGLE_USER_MAPPER` (a dotted-path `(id_info, user, created) -> None` hook).
    - **System check** — `manage.py check` warns (`django_gauth.W001`–`W003`) when
      integration is enabled but `django.contrib.auth`, `AuthenticationMiddleware`, or
      `GoogleAuthBackend` is missing.

    See [Django User Integration](https://masterpiece93.github.io/django-gauth/concepts/django-user-integration/).
- **Redirection Schemes (issue #77)** — nested & dynamic Google auth, out of the box.
  `login()` now accepts a `?scheme=` query parameter that controls how the post-auth
  destination is resolved, so users can be sent back to the exact page they
  authenticated from:
    - `PRESERVE_ORIGIN_QP` — origin read from the `origin_url` query parameter.
    - `PRESERVE_ORIGIN_HP` — origin read from the `X-ORIGIN-URL` request header.
    - `LANDING_PAGE` — uses `GOOGLE_AUTH_FINAL_REDIRECT_URL` (or the package index).
    - `DEFAULT` — alias for `LANDING_PAGE` (used when no `scheme` is supplied).

  Origin URLs are validated as **same-origin** to prevent open-redirect attacks;
  cross-origin or malformed values fall back to the landing page. A new
  `RedirectionScheme` enum is exported from `django_gauth.utilities`.
- **Configurable response type for `login()`** — a new `?response=` query parameter
  selects how the Google authorization URL is delivered: `redirect` (default, a `302`)
  or `json` (a `JsonResponse` of `{"redirect_to": ...}`). The JSON form lets a
  Single-Page Application drive the top-level navigation itself, which is **required**
  for the `PRESERVE_ORIGIN_HP` scheme (a custom header can only be sent via `fetch`, and
  a `fetch` cannot land on Google's consent screen). Invalid `scheme`/`response` values
  return a clear `400`.
- `GOOGLE_LOGIN_PROMPT` setting — the Google consent screen `prompt` parameter is now
  configurable. Default value: `"select_account consent"`. Accepted values:
  `select_account`, `consent`, `select_account consent`, `none`.
- **Session Lifecycle Management (issue #86)** — first-class support for keeping a
  session alive past Google's ~1 hour ID-token lifetime, plus a clean logout:
    - **`logout()` view** (`/gauth/logout/`) — clears the session (rotating the session
      key via `flush()`) and, by default, **best-effort revokes the upstream Google
      token** so access is withdrawn on Google's side too. Mirrors `login()`'s
      `?response=` convention (`redirect` → `302`, `json` → `{"status": "logged_out"}`).
      A revocation failure never blocks logout — the local session is always cleared.
    - **`session_status()` probe** (`/gauth/session`) — a JSON endpoint an SPA can poll
      to read the current auth state: `{"authenticated": bool, "user": {...} | null}`.
      It **transparently refreshes** the Google access token (and cached `id_info`) when
      it has expired but a `refresh_token` is available, so the session survives the
      1-hour ID-token expiry.
    - **`get_credentials(request)` accessor** — the reusable building block behind the
      probe. Returns valid `Credentials` for the request, silently refreshing and
      re-verifying a fresh `id_token` when needed, and writing the refreshed credentials
      and `id_info` back to the session.
    - **`revoke_google_token(token)` helper** — best-effort POST to Google's
      `revoke` endpoint; returns a `bool` and swallows transport errors.
    - **`get_session_expiry(session)` helper** — a **read-only** accessor that returns the
      effective session deadline and its governing policy
      (`{"expires_at", "policy", "expired"}`, earliest of token / max-age / idle) without
      mutating the session. Powers the landing page's "Session Expiring In" countdown.
    - **Configurable session policy** — three composable settings let you place
      the session anywhere from "indefinite rolling" to "force periodic re-login":
      `GOOGLE_SESSION_AUTO_REFRESH` (default `True`; `False` disables silent
      refresh so the session ends at ID-token expiry), `GOOGLE_SESSION_MAX_AGE`
      (default `None`; absolute cap in seconds, enforced even when a valid refresh
      token exists), and `GOOGLE_SESSION_IDLE_TIMEOUT` (default `None`; idle cap in
      seconds). The caps are independent and additive, and are enforced by
      `get_credentials()` / the `/gauth/session` probe. Defaults preserve the
      previous always-refresh behaviour.
    - Logout settings — `GOOGLE_TOKEN_REVOKE_ON_LOGOUT` (default `True`) and
      `GOOGLE_AUTH_LOGOUT_REDIRECT_URL` (default `None` → package index).

### Changed

- `GOOGLE_AUTH_FINAL_REDIRECT_URL` system check now validates URL format using URL
  parsing: a non-empty value that lacks a scheme or host (e.g. a bare relative path
  like `"/dashboard/"`) produces an `Info`-level system check entry. Empty string and
  `None` are silently treated as "not configured" and produce no entry. Previously any
  falsy value — including `""` — triggered the check.
- **Landing page is now session-policy aware.** The built-in `/gauth/` index resolves its
  authenticated state through `get_credentials()` (rather than a raw token check), so it
  agrees with `@gauth_required` and `/gauth/session`. It now surfaces a **Logout button**
  beside the Authenticate button, an *effective-deadline* countdown (earliest of token /
  max-age / idle), and a targeted "session expired" message naming the governing policy.

### Fixed

- **`callback()` no longer crashes when Google narrows the granted scopes** (e.g. after a
  logout that revoked the token, a sensitive scope requiring re-consent is dropped). The
  token exchange now tolerates a reduced scope set and logs a warning instead of raising
  `Warning: Scope has changed …`.
- **A re-login now reliably restores an expired session.** `callback()` resets the idle
  clock (`gauth_last_active`) alongside the login timestamp, so a stale value left over
  from a previously idle/expired session can no longer immediately re-expire the fresh
  one under `GOOGLE_SESSION_IDLE_TIMEOUT`.
- **`session_status()` authenticated state matches the guards.** With Django User
  integration enabled, the probe's `authenticated` flag is sourced from
  `request.user.is_authenticated`, so it agrees with `@gauth_required` and
  `@login_required` instead of reporting on the Google token alone.
- **Landing-page countdown** no longer displays sub-second (micro/nanosecond) digits.

## [0.2.2] - 2026-06-29

### Added

- Repository hygiene files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`.
- GitHub issue templates (`bug_report.yml`, `feature_request.yml`, `config.yml`) and a
  pull request template.

### Fixed

- Callback scope mismatch: `callback()` now uses `settings.SCOPE` instead of a hardcoded
  scope list (which included `.../auth/drive`), preventing confusing "Scope has changed"
  errors when a custom `SCOPE` is configured.
- Security: the OAuth `client_secret` (and `client_id`) are no longer persisted in the
  session store. `credentials_to_dict()` omits them and `check_gauth_authentication()`
  re-injects them from settings when rebuilding `Credentials`.
- Robustness: `callback()` now reads the public `credentials.id_token` property instead of
  the private `credentials._id_token` attribute, avoiding breakage on future `google-auth`
  releases.
- Friendly state-mismatch handling: `callback()` explicitly compares the returned `state`
  with the session value and returns a clear `400` (instead of an opaque oauthlib stack
  trace) when it is missing or mismatched — guarding against CSRF, expired sessions, and
  replayed callback links.
- Callback error-path handling: `callback()` now detects provider errors (e.g. the user
  clicking *Deny* → `?error=access_denied`) and redirects gracefully to the configured
  landing page instead of crashing on a missing authorization `code`.

---

## [0.2.1] - 2026-06-25

### Added

- Extended unit tests (`tests/test_coverage_boost.py`) raising coverage from 37% → **99%**.
- Comprehensive MkDocs documentation with Mermaid diagrams, admonitions, tabs, and annotations.
- New documentation pages: Installation, Google Cloud Setup, OAuth2 Explained, Architecture,
  Settings Reference, URL Configuration, UI Customization, Production Deployment,
  Troubleshooting, API (Views/Utilities/Checks), Flows, and Changelog.
- Detailed `ErrorCodes` reference with flowcharts, fix examples, and terminal output previews.
- `pdm.lock` explanation section in `dev.README.md` with a cross-link from `README.md`.

### Changed

- Fixed `runtests.py` to start coverage **before** `django.setup()` for accurate
  module-level tracking.
- Moved `dev` and `lint` extras from `[project.optional-dependencies]` to
  `[dependency-groups]` (internal-only, not user-facing).
- Repaired corrupted `pip` in `test-venv` (circular import in vendored `pyparsing`).
- Uncommented `.vscode/` in `.gitignore` to exclude editor-specific config from version control.

### Removed

- `google-api-python-client` from runtime dependencies (confirmed unused in source).
- `mypy` from runtime dependencies (dev-only tool; remains in `[dependency-groups]`).

---

## [0.2.0] - 2025-11-12

### Added

- System checks for all required settings (startup validation).
- Debug endpoint (available when `DEBUG=True`).
- Origin URL validation for secure redirects.
- UI customization via `DJANGO_GAUTH_UI_CONFIG`.

### Changed

- Improved dependency version constraints with Python version markers.
- Enhanced documentation with comprehensive guides and diagrams.

---

## [0.1.2] - 2025-09-24

### Added

- `pypi.README.md` as the dedicated PyPI project description.
- Additional Trove classifiers (`Topic`, `Typing :: Typed`, development status
  `Production/Stable`).
- Release workflow support for publishing to PyPI.

### Changed

- Refined project keywords and package description.

### Removed

- Mention of Python 3.8 support from classifiers.
- Legacy `README.rst` in favor of `pypi.README.md`.

---

## [0.1.1] - 2025-09-22

### Changed

- Corrected the license Trove classifier.
- Packaging metadata tweaks in `pyproject.toml`.
- Made the release workflow more verbose for easier debugging.

---

## [0.1.0] - 2025-09-22

### Added

- Initial public release.
- Google OAuth2 authentication flow (discovery-based).
- Built-in landing page with an authentication button.
- Session-based credential storage.
- Django admin integration for session management.
- Support for Django 3.1 – 5.2 and Python 3.9 – 3.12.

---

[Unreleased]: https://github.com/masterPiece93/django-gauth/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/masterPiece93/django-gauth/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/masterPiece93/django-gauth/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/masterPiece93/django-gauth/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/masterPiece93/django-gauth/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/masterPiece93/django-gauth/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/masterPiece93/django-gauth/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/masterPiece93/django-gauth/releases/tag/v0.1.0
