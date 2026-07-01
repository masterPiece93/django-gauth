---
title: Changelog
description: Version history and release notes.
tags:
  - changelog
  - releases
---

# Changelog :material-history:

All notable changes to this project are documented here.

---

## Unreleased

### Added

- **Redirection Schemes (issue #77)** — nested & dynamic Google auth out of the box.
  `login()` accepts a `?scheme=` query parameter (`PRESERVE_ORIGIN_QP`,
  `PRESERVE_ORIGIN_HP`, `LANDING_PAGE`, `DEFAULT`) that sends users back to the exact
  page they authenticated from. Origins are same-origin validated to prevent
  open-redirect attacks. See
  [Redirection Schemes](concepts/redirection-schemes.md).
- **Configurable `login()` response type** — a `?response=` parameter selects `redirect`
  (default `302`) or `json` (`{"redirect_to": ...}`) delivery of the authorization URL.
  The JSON form lets an SPA drive the top-level navigation itself, and is required for the
  `PRESERVE_ORIGIN_HP` scheme.

### Security

- **`oauth_state` cleared after successful auth** — `callback()` now explicitly removes
  the OAuth2 CSRF nonce from the session once authentication completes. It is a
  single-use token and has no purpose after the token exchange; clearing it prevents
  stale CSRF material from persisting in the authenticated session. Error paths
  (state-mismatch `400`, `access_denied` redirect) intentionally retain it to allow retry.

### Changed

- **`GOOGLE_AUTH_FINAL_REDIRECT_URL` validation** — The startup system check now uses URL
  parsing to validate the configured value. A non-empty string that lacks a scheme or host
  (e.g. a bare relative path like `"/dashboard/"`) produces an `Info`-level system check
  entry. Empty string and `None` are silently treated as "not configured". Use a
  fully-qualified URL (`https://myapp.example.com/dashboard/`) to keep system checks clean.

---

## v0.2.2

:material-calendar: 2026-06-29

### Fixed

- **Callback scope mismatch** — `callback()` now uses `settings.SCOPE` instead of a hardcoded scope list, preventing "Scope has changed" errors when a custom `SCOPE` is configured.
- **`client_secret` no longer stored in session** — `credentials_to_dict()` omits `client_id`/`client_secret`; they are re-injected from settings when rebuilding `Credentials`.
- **Public `id_token` accessor** — reads `credentials.id_token` instead of the private `credentials._id_token`, avoiding breakage on future `google-auth` releases.
- **Friendly state-mismatch handling** — `callback()` compares the returned `state` with the session value and returns a clear `400` instead of an opaque stack trace.
- **Callback error-path handling** — provider errors (e.g. user clicks *Deny* → `?error=access_denied`) redirect gracefully instead of crashing.

### Added

- Repository hygiene files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue templates, and a pull request template.

---

## v0.2.1

:material-calendar: 2026-06-25

### Changed

- Removed `google-api-python-client` from runtime dependencies (unused)
- Removed `mypy` from runtime dependencies (dev-only tool)
- Moved `dev` and `lint` extras from `[project.optional-dependencies]` to `[dependency-groups]` (internal-only, not user-facing)
- Fixed `runtests.py` to start coverage before `django.setup()` for accurate module-level tracking
- Repaired corrupted `pip` in `test-venv` (circular import in vendored `pyparsing`)
- Uncommented `.vscode/` in `.gitignore` to exclude editor-specific config from version control

### Added

- Extended test coverage to **99%**
- Comprehensive MkDocs documentation with Mermaid diagrams, admonitions, tabs, and annotations
- New docs pages: Installation, Google Cloud Setup, OAuth2 Explained, Architecture, Settings Reference, URL Configuration, UI Customization, Production Deployment, Troubleshooting, API Views/Utilities/Checks, Flows, Changelog
- Detailed `ErrorCodes` reference in docs with flowcharts, fix examples, and terminal output previews
- `pdm.lock` explanation section in `dev.README.md` with cross-link from `README.md`
- Extended unit tests (`test_coverage_boost.py`) raising coverage from 37% → 99%

### Removed

- `google-api-python-client` from runtime dependencies (confirmed unused in source)
- `mypy` from runtime dependencies (dev-only tool, remains in `[dependency-groups]`)

---

## v0.2.0

:material-calendar: Latest

### Changed

- Improved dependency version constraints with Python version markers
- Enhanced documentation with comprehensive guides and diagrams

### Added

- System checks for all required settings
- Debug endpoint (when `DEBUG=True`)
- Origin URL validation for secure redirects
- UI customization via `DJANGO_GAUTH_UI_CONFIG`

---

## v0.1.2

### Added

- Initial public release
- Google OAuth2 authentication flow
- Built-in landing page with authentication button
- Session-based credential storage
- Django admin integration for session management
- Support for Django 3.1 — 5.2
- Support for Python 3.9 — 3.12

---

## Links

- [PyPI](https://pypi.org/project/django-gauth/)
- [GitHub Releases](https://github.com/masterPiece93/django-gauth/releases)
