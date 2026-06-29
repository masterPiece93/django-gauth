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

### Added

- Repository hygiene files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`.
- GitHub issue templates (`bug_report.yml`, `feature_request.yml`, `config.yml`) and a
  pull request template.

### Fixed

- Callback scope mismatch: `callback()` now uses `settings.SCOPE` instead of a hardcoded
  scope list (which included `.../auth/drive`), preventing confusing "Scope has changed"
  errors when a custom `SCOPE` is configured.

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

[Unreleased]: https://github.com/masterPiece93/django-gauth/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/masterPiece93/django-gauth/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/masterPiece93/django-gauth/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/masterPiece93/django-gauth/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/masterPiece93/django-gauth/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/masterPiece93/django-gauth/releases/tag/v0.1.0
