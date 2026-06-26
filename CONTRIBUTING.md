# Contributing to django-gauth

First off — thank you for taking the time to contribute! 🎉

`django-gauth` is a small, focused Django app that adds Google's discovery-based OAuth2
authentication to HTTP/HTTPS Django projects. Contributions of all kinds are welcome: bug
reports, documentation fixes, tests, and features.

- 📦 **PyPI:** https://pypi.org/project/django-gauth/
- 📖 **Docs:** https://masterpiece93.github.io/django-gauth/
- 🐙 **Source:** https://github.com/masterPiece93/django-gauth

Please also read our [Code of Conduct](./CODE_OF_CONDUCT.md). For security issues, **do not**
open a public issue — follow [SECURITY.md](./SECURITY.md) instead.

---

## Table of Contents

- [Ways to Contribute](#ways-to-contribute)
- [Project Layout](#project-layout)
- [Development Environment](#development-environment)
- [Running the Tests](#running-the-tests)
- [Linting, Formatting & Typing](#linting-formatting--typing)
- [Building the Documentation](#building-the-documentation)
- [Building the Package](#building-the-package)
- [Trying It in a Real Project (DevPlatform)](#trying-it-in-a-real-project-devplatform)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Commit Messages](#commit-messages)
- [Reporting Bugs & Requesting Features](#reporting-bugs--requesting-features)

---

## Ways to Contribute

- **Report a bug** using the [bug report template](./.github/ISSUE_TEMPLATE/bug_report.yml).
- **Request a feature** using the [feature request template](./.github/ISSUE_TEMPLATE/feature_request.yml).
- **Improve docs** — anything under `docs/` (built with MkDocs Material).
- **Add tests** — we aim to keep coverage high (currently ~99%).
- **Fix a bug or implement a feature** — see the open issues and the project roadmap.

> 💡 For anything larger than a small fix, please open an issue first so we can discuss the
> approach before you invest time in a pull request.

---

## Project Layout

| Path | Purpose |
|------|---------|
| `src/django_gauth/` | The installable package (views, utilities, urls, checks, etc.) |
| `tests/` | Test suite (`runtests.py` discovers these) |
| `docs/` | MkDocs documentation source |
| `devPlatform/` | A throwaway Django project for manual testing of the app |
| `runtests.py` | Standalone test runner with coverage |
| `noxfile.py` / `nox.sh` | Multi-version (Django × Python) test sessions |
| `pyproject.toml` | Project metadata, dependencies, and tool config |
| `dev.README.md` | In-depth maintainer notes (this file is the friendly summary) |

---

## Development Environment

The project uses **[PDM](https://pdm-project.org/)** (installed via
[pipx](https://pipx.pypa.io/)) for dependency and workflow management. A more detailed guide
lives in [`dev.README.md`](./dev.README.md); the essentials are below.

### 1. Install pipx and PDM

```sh
# Install pipx, then ensure it is on PATH
pipx ensurepath

# Install PDM with a project-specific suffix
pipx install --suffix "@djangoGauth" pdm --python python3.12

# Confirm it is available (look for `pdm@djangoGauth`)
pipx list
```

### 2. Install dependencies

If `pdm.lock` exists (it does), sync from it for a reproducible environment:

```sh
pdm@djangoGauth sync
```

Otherwise, install dependency groups directly:

```sh
# Everything
pdm@djangoGauth install -G :all

# Only linting tools
pdm@djangoGauth install -G lint

# Only dev/build tools
pdm@djangoGauth install -G dev
```

> ℹ️ `pdm.lock` is for **contributors** to get reproducible environments. End users installing
> from PyPI resolve dependencies from `pyproject.toml` and Python version markers — see the
> note in [`dev.README.md`](./dev.README.md#why-pdmlock-exists-in-this-project).

---

## Running the Tests

All tests live in the `tests/` folder. The fastest path is the standalone runner inside a
lightweight virtualenv.

```sh
# 1. Create and activate an isolated test environment
python3 -m venv test-venv
source test-venv/bin/activate

# 2. Install the test requirements
pip install -r tests/requirements.txt

# 3. Run the suite (with coverage + HTML report in htmlcov/)
python3 runtests.py
```

`runtests.py` spins up a minimal in-memory Django project, runs the suite, and prints a
coverage report.

### Automation tests

Some optional automation tests live alongside the unit tests and are **off by default**.
Toggle them with the `AUTOMATION` environment variable:

```sh
export AUTOMATION="1"   # turn ON
unset AUTOMATION        # turn OFF (default)
```

### Multi-version testing with nox

To test across supported Django and Python versions:

```sh
# Django test runner across versions
./nox.sh -s test_django_versions__runner

# pytest across versions
./nox.sh -s test_django_versions__pytest
```

> ✅ Please make sure tests pass and add tests for any new behavior before opening a PR.

---

## Linting, Formatting & Typing

We use **ruff**, **black**, **isort**, **vulture**, **pylint**, and **mypy**, all wired into
PDM scripts (see `[tool.pdm.scripts]` in `pyproject.toml`).

```sh
pdm@djangoGauth format   # auto-format (isort + black)
pdm@djangoGauth lint     # vulture + ruff + import/format checks
pdm@djangoGauth fix      # auto-fix ruff issues
pdm@djangoGauth pylint   # pylint
pdm@djangoGauth mypy     # static type checking
```

The `pylint` GitHub Action runs:

```sh
pylint $(git ls-files '*.py') --disable=C0114,C0116 --fail-under=9.0
```

> 🧹 Run `pdm@djangoGauth format` and `pdm@djangoGauth lint` before committing.

---

## Building the Documentation

Docs are built with **MkDocs Material**.

```sh
# In a venv with mkdocs installed:
pip install mkdocs mkdocs-material

# Live preview at http://127.0.0.1:8000
mkdocs serve

# Strict build (treats warnings as errors — matches CI)
mkdocs build --strict
```

> 📝 If you change behavior or settings, please update the relevant page under `docs/`.

---

## Building the Package

```sh
pdm@djangoGauth build         # build sdist + wheel into dist/
pdm@djangoGauth check_build   # verify wheel contents
```

Always lint, type-check, and run tests before building a release artifact.

---

## Trying It in a Real Project (DevPlatform)

`devPlatform/` is a minimal Django project for manually exercising the app:

```sh
cd devPlatform/

# First-time setup
make all

# Subsequent runs
make runserver
```

This installs `django_gauth` in editable mode, so local changes are reflected immediately.

---

## Pull Request Guidelines

Before you open a PR, please make sure:

1. ✅ Tests pass locally (`python3 runtests.py`).
2. ✅ New behavior is covered by tests.
3. ✅ `pdm@djangoGauth lint` and `pdm@djangoGauth mypy` are clean.
4. ✅ Documentation is updated for any user-facing change.
5. ✅ The PR description explains **what** changed and **why**.

Fill out the [pull request template](./.github/PULL_REQUEST_TEMPLATE.md) — it includes this
checklist. Keep PRs focused: one logical change per PR is much easier to review.

---

## Commit Messages

Write clear, imperative commit messages:

```
Fix callback scope mismatch with settings.SCOPE

The callback hardcoded scopes that differed from login(), which caused
"Scope has changed" errors for custom SCOPE configurations.
```

Conventional-commit-style prefixes (`fix:`, `feat:`, `docs:`, `test:`, `chore:`) are welcome
but not required.

---

## Reporting Bugs & Requesting Features

- 🐛 **Bugs:** use the [bug report template](./.github/ISSUE_TEMPLATE/bug_report.yml). Include
  your `django-gauth`, Python, and Django versions and a minimal reproduction.
- ✨ **Features:** use the [feature request template](./.github/ISSUE_TEMPLATE/feature_request.yml).
- 🔐 **Security:** **never** file a public issue — follow [SECURITY.md](./SECURITY.md).

> ⚠️ When sharing logs or config, **redact all secrets** — never paste real client IDs,
> client secrets, tokens, or authorization codes.

Thanks again for contributing! 💙
