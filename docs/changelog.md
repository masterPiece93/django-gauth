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

## v0.2.1

:material-calendar: 2025-06-25

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
