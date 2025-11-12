"""
Nox configuration file for testing django-gauth package across multiple Python and Django versions.

This file defines sessions for running tests in isolated virtual environments using Nox. 
It supports a matrix of Python and Django versions to ensure compatibility and proper functionality.

Features:
- Matrix testing for Python versions: 3.9, 3.10, 3.11, 3.12, 3.13.
- Matrix testing for Django versions: 4.2, 5.0, 5.1, 5.2.
- Dynamic installation of dependencies using PDM.
- Skips incompatible Python-Django combinations.

Usage:
Run `nox` to execute all sessions or specify a session using `nox -s <session_name>`.
"""

import nox
import os

# Define the Python versions you want to test with
# NOTE: Use pyenv for maintaining multiple Python versions
python_versions = ["3.9", "3.10", "3.11", "3.12", "3.13"]
# Define the Django versions you want to test against
# NOTE: These will be installed dynamically
django_versions = ["3.1", "4.2", "5.0", "5.1", "5.2"]  # Consult pytest-django docs for compatibility

def embed_link(uri, label=None):
    """
    Escapes a hyperlink for console output using ANSI escape codes.

    Args:
        uri (str): The URL to embed.
        label (str, optional): The label to display for the link. Defaults to the URL.

    Returns:
        str: The formatted hyperlink string.

    Example:
        print(embed_link("https://www.google.com", "Google"))
        print(embed_link("https://www.python.org"))
    """
    if label is None:
        label = uri
    # ANSI escape code for a hyperlink
    return f"\033]8;;{uri}\033\\{label}\033]8;;\033\\"

def invalid_python_to_django(django_version, python_version):
    return (
        (django_version in ["5.0", "5.1", "5.2"] and python_version in {"3.8", "3.9"}) or
        (django_version == "3.0" and python_version not in {"3.6", "3.7", "3.8", "3.9"}) or
        (django_version == "3.1" and python_version not in {"3.6", "3.7", "3.8", "3.9"}) or
        (django_version == "3.2" and python_version not in {"3.6", "3.7", "3.8", "3.9", "3.10"}) or
        (django_version == "3.2" and python_version not in {"3.6", "3.7", "3.8", "3.9", "3.10"}) or
        (django_version == "4.2" and python_version not in {"3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13"})
    )

@nox.session(python=python_versions)
@nox.parametrize("django", django_versions)
def test_django_versions__pytest(session: nox.Session, django: str):
    """
    Test the project with a matrix of Python and Django versions.

    This Nox session runs tests for the `django-gauth` package across multiple Python and Django versions 
    to ensure compatibility and proper functionality.

    Args:
        session (nox.Session): The Nox session object, which provides an isolated virtual environment.
        django (str): The Django version to test against.

    Behavior:
    - Skips incompatible Python-Django combinations (e.g., Django 5.x with Python 3.9).
    - Installs the project and its dependencies using `pip`.
    - Dynamically installs the specified Django version.
    - Installs additional testing dependencies such as `pytest` and `pytest-django`.
    - Runs the test suite using `pytest`.

    Environment Variables:
    - `GOOGLE_CLIENT_ID`: Required for tests that depend on Google OAuth.
    - `GOOGLE_CLIENT_SECRET`: Required for tests that depend on Google OAuth.

    Examples:
    Run all sessions:
        nox

    Run a specific session for Django 5.0:
        nox -s test_django_versions -- 5.0
    """
    # Skip a specific combination
    if invalid_python_to_django(django, session.python):
        django_compatibility_faq = "https://docs.djangoproject.com/en/5.2/faq/install/#what-python-version-can-i-use-with-django"
        session.skip(f"Skipping Django {django} with Python {session.python}. {embed_link(django_compatibility_faq, 'FAQ')}")

    # Install Self
    session.install(f".")

    # Install the specified Django version dynamically
    session.install(f"Django=={django}")

    # Install additional dependencies required for testing
    session.install("environs")  # For environment variable management
    session.install("django-environ")
    
    session.install("selenium")
    session.install("undetected-chromedriver")
    session.install("setuptools")

    session.install("pytest")  # Pytest :Test runner
    session.install("pytest-django")  # Pytest :Plugin Django-specific
    
    NOX_RUNTIME_ENV = {
        "AUTOMATION": "0",  # Google OAuth client ID
        "ENV_PATH": "/home/ubuntu/Documents/personal/django-gauth/tests/.env.test",  # Google OAuth client secret
        "GOOGLE_CLIENT_ID": os.environ["GOOGLE_CLIENT_ID"],  # Google OAuth client ID
        "GOOGLE_CLIENT_SECRET": os.environ["GOOGLE_CLIENT_ID"]  # Google OAuth client secret
    }
    # Run Pytest
    session.run("pytest", env=NOX_RUNTIME_ENV)

@nox.session(python=python_versions)
@nox.parametrize("django", django_versions)
def test_django_versions__runner(session: nox.Session, django: str):
    """
    Test the project with a matrix of Python and Django versions.

    This Nox session runs tests for the `django-gauth` package across multiple Python and Django versions 
    to ensure compatibility and proper functionality.

    Args:
        session (nox.Session): The Nox session object, which provides an isolated virtual environment.
        django (str): The Django version to test against.

    Behavior:
    - Skips incompatible Python-Django combinations (e.g., Django 5.x with Python 3.9).
    - Installs the project and its dependencies using `pip`.
    - Dynamically installs the specified Django version.
    - Installs additional testing dependencies such as `pytest` and `pytest-django`.
    - Runs the test suite using `pytest`.

    Environment Variables:
    - `GOOGLE_CLIENT_ID`: Required for tests that depend on Google OAuth.
    - `GOOGLE_CLIENT_SECRET`: Required for tests that depend on Google OAuth.

    Examples:
    Run all sessions:
        nox

    Run a specific session for Django 5.0:
        nox -s test_django_versions -- 5.0
    """
    # Skip a specific combination
    if invalid_python_to_django(django, session.python):
        django_compatibility_faq = "https://docs.djangoproject.com/en/5.2/faq/install/#what-python-version-can-i-use-with-django"
        session.skip(f"Skipping Django {django} with Python {session.python}. {embed_link(django_compatibility_faq, 'FAQ')}")

    # Install Self
    session.install(f".")

    # Install the specified Django version dynamically
    session.install(f"Django=={django}")

    # Install additional dependencies required for testing
    session.install("environs")  # For environment variable management
    session.install("django-environ")
    
    session.install("selenium")
    session.install("undetected-chromedriver")
    session.install("setuptools")

    NOX_RUNTIME_ENV = {
        "AUTOMATION": "0",  # Google OAuth client ID
        "ENV_PATH": "/home/ubuntu/Documents/personal/django-gauth/tests/.env.test",  # Google OAuth client secret
    }
    # Run Django Test runner
    session.run("python3", "runtests", env=NOX_RUNTIME_ENV)

