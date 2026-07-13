# AGENTS.md - Guide for AI-Assisted Development

This file is the definitive system-instruction contract for any AI agent operating on the **django-gauth** codebase. Every agent **must** read this file in full and strictly adhere to its rules **before** reading, modifying, testing, or publishing any code in this repository.

---

## 🗺️ Codebase Map

| Path | Description |
|------|-------------|
| `src/django_gauth/` | The installable package (the only code that ships to PyPI). |
| `src/django_gauth/apps.py` | `AppConfig`; applies setting defaults via `apply_setting_defaults()` + registers system checks. |
| `src/django_gauth/views.py` | OAuth2 flow views (`index`, `callback`, login/logout). |
| `src/django_gauth/utilities.py` | Credential/session helpers (`get_credentials`, `get_session_expiry`, session-policy logic). |
| `src/django_gauth/decorators.py` | `gauth_required` and related access-control decorators. |
| `src/django_gauth/backends.py` | Authentication backend integration. |
| `src/django_gauth/_checks.py` | Implementation of Django system checks (compatibility/settings/user-integration). |
| `src/django_gauth/defaults.py` | Canonical default values for optional settings. |
| `src/django_gauth/urls.py` | URL routes exposed by the app. |
| `src/django_gauth/templates/` & `static/` | Bundled UI (landing page, buttons, assets). |
| `src/django_gauth/py.typed` | PEP 561 marker — package ships type information. |
| `tests/` | Test suite (`runtests.py` target); `test_coverage_boost.py`, `test_oauth2_flow.py`, `test_settings.py`. |
| `runtests.py` | Django `DiscoverRunner` entrypoint that starts `coverage` **before** `django.setup()`. |
| `noxfile.py` / `nox.sh` | Matrix testing across Python 3.9–3.13 and Django 3.1–5.2. |
| `devPlatform/` | Throwaway host Django project for manual local runs (never shipped). |
| `docs/` + `mkdocs.yml` | MkDocs Material documentation source. |
| `pyproject.toml` | Single source of truth for version, deps, build backend, and all tool config. |
| `CHANGELOG.md` / `docs/changelog.md` | Keep-a-Changelog history (must be kept in sync). |

> The package **version lives only in `pyproject.toml`** — there is intentionally **no** `__version__` in `__init__.py`. Do not add one.

---

## 📦 Environment & Dependency Management

- **Primary manager:** **PDM**, installed via `pipx` with a suffix wrapper. The command is `pdm@djangoGauth` (bare `pdm` is **not** on `PATH`).
- **Nox** is installed similarly and invoked through the `./nox.sh` wrapper (which loads `tests/.env.test` first).
- Lightweight throwaway **venvs** are used for isolated tasks: `test-venv/` (test runner), `lint-venv/` (linters), `venv/` (docs).

Canonical invocations:

```bash
# Install dependency groups (dev, lint, or all)
pdm@djangoGauth install -G :all
pdm@djangoGauth sync          # when pdm.lock already exists

# Run the fast test suite (Django runner + coverage)
GOOGLE_CLIENT_ID=ci-dummy GOOGLE_CLIENT_SECRET=ci-dummy AUTOMATION=0 \
  ./test-venv/bin/python runtests.py

# Multi-version matrix (Python x Django)
./nox.sh -s test_django_versions__runner
./nox.sh -s test_django_versions__pytest

# Docs
./venv/bin/mkdocs build --clean --strict
```

- `pdm.lock` is for **contributor reproducibility only**; end-user resolution comes from `[project].dependencies` in `pyproject.toml`.
- Never assume a global interpreter — always run through the correct wrapper/venv shown above.

---

## 🛠️ Build and Test Procedures

**Test suite (required before every change is considered done):**

```bash
GOOGLE_CLIENT_ID=ci-dummy GOOGLE_CLIENT_SECRET=ci-dummy AUTOMATION=0 \
  ./test-venv/bin/python runtests.py     # 100% coverage is the standing baseline
```

- Selenium automation tests (`tests/test_oauth2_flow.py::GoogleOAuthTest`) are gated behind `AUTOMATION=1` and are **off** by default. An `OSError: [Errno 98] Address already in use` from them is environmental, not a real failure.

**Lint / format / type checks (via PDM scripts defined in `pyproject.toml`):**

```bash
pdm@djangoGauth lint      # composite: vulture + ruff + isort --check + black --check
pdm@djangoGauth format    # isort + black (writes changes)
pdm@djangoGauth fix       # ruff --fix
pdm@djangoGauth pylint    # pylint -f actions src/
pdm@djangoGauth mypy      # mypy src/
```

**Tooling in play:** `ruff` (line-length 99), `black` (line-length 88), `isort` (black profile), `mypy` (strict for `django_gauth.*`: `disallow_untyped_defs`), `pylint` (max-line 100), `vulture`, `codespell`, `validate-pyproject`.

> ⛔ **Absolute rule:** An agent must **never** weaken, delete, or edit a test assertion merely to make failing code pass. Tests encode intended behavior. If a test fails, fix the production code — or, if the test itself is genuinely wrong, stop and surface the discrepancy to a human for confirmation before changing it. Coverage must not regress below the existing baseline.

---

## 📝 Architectural & Code Quality Style Rules

- **Target Python:** `requires-python = ">=3.9"`. All shipped code must run on **3.9 through 3.13**. Do not use syntax/stdlib features newer than 3.9 (mypy is pinned to analyze at `python_version = "3.12"`, but runtime support starts at 3.9).
- **Django support:** 3.1 through 5.2 — never rely on APIs unavailable in that whole range.
- **Typing is mandatory:** every function/method in `src/django_gauth/` must carry complete type hints; `disallow_untyped_defs` is enforced for `django_gauth.*`. The package is typed (`py.typed`) — keep it accurate.
- **Docstrings:** public modules, functions, and classes use clear, imperative docstrings (Google-style arg/return sections where parameters exist), consistent with existing files like `noxfile.py` and `apps.py`.
- **Function design:** keep functions single-purpose and small; avoid deep nesting (prefer early returns — the repo enables flake8-return). Extract helpers rather than growing monoliths (e.g., `apply_setting_defaults()` was extracted from a system check for exactly this reason).
- **Settings discipline:** runtime defaults are applied in `AppConfig.ready()` via `apply_setting_defaults()` (runs under gunicorn/uWSGI/ASGI), **not** as a side effect of a system check. System checks are for *validation/reporting only* — never mutate state inside them as the primary mechanism.
- **Changelog parity:** any user-facing change updates **both** `CHANGELOG.md` and `docs/changelog.md` under `[Unreleased]`, following Keep a Changelog + SemVer.
- Respect all ignore lists and per-file rules already configured in `pyproject.toml`; do not silence lint errors ad hoc without justification.

---

## 🚀 PyPI Packaging & Publishing Flow

- **Build backend:** `setuptools>=61` (`build-system` in `pyproject.toml`). Package metadata, classifiers, and dependencies all live in `pyproject.toml`.
- **Versioning:** bump `[project].version` in `pyproject.toml` **only** (Semantic Versioning). Patches (e.g. `0.3.1`) ship from the `[Unreleased]` changelog section, which is then renamed to the version + date on release.

**Release steps:**

```bash
# 1. Validate metadata and quality gates first
validate-pyproject pyproject.toml
pdm@djangoGauth lint && pdm@djangoGauth mypy
GOOGLE_CLIENT_ID=ci-dummy GOOGLE_CLIENT_SECRET=ci-dummy AUTOMATION=0 \
  ./test-venv/bin/python runtests.py

# 2. Build the sdist + wheel
pdm@djangoGauth build

# 3. Verify the built artifacts
pdm@djangoGauth check_build        # check-wheel-contents dist/

# 4. Publish (twine)
twine upload dist/*
```

- Only content under `src/django_gauth/` (plus declared package data: templates, static, `py.typed`) ships. Confirm no dev-only files (e.g. `prompt.md`, `devPlatform/`) leak into the sdist/wheel via `check_build`.
- Use only official [PyPI classifiers](https://pypi.org/classifiers/) — invalid classifiers fail the upload.
- Always run `lint`, `mypy`, and the full test suite **before** building a release artifact.

---

> **Agent compliance note (AAIF best practices):** operate transparently, make the smallest correct change, gather file context before editing, keep changes reversible, never fabricate test results, and never bypass the quality gates above. When a requested action conflicts with these rules, pause and escalate to a human maintainer.
