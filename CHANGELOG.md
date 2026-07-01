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

### Changed

- `GOOGLE_AUTH_FINAL_REDIRECT_URL` system check now validates URL format using URL
  parsing: a non-empty value that lacks a scheme or host (e.g. a bare relative path
  like `"/dashboard/"`) produces an `Info`-level system check entry. Empty string and
  `None` are silently treated as "not configured" and produce no entry. Previously any
  falsy value — including `""` — triggered the check.

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

[Unreleased]: https://github.com/masterPiece93/django-gauth/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/masterPiece93/django-gauth/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/masterPiece93/django-gauth/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/masterPiece93/django-gauth/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/masterPiece93/django-gauth/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/masterPiece93/django-gauth/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/masterPiece93/django-gauth/releases/tag/v0.1.0
