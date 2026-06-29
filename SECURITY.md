# Security Policy

`django-gauth` handles authentication via Google's OAuth2, so we take security reports
seriously. Thank you for helping keep the project and its users safe.

---

## Supported Versions

Security fixes are applied to the latest released version. We recommend always running the
most recent release from [PyPI](https://pypi.org/project/django-gauth/).

| Version | Supported |
|---------|:---------:|
| `0.2.x` | ✅ |
| `< 0.2` | ❌ |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or
pull requests.**

Instead, report them privately using **one** of the following:

1. **GitHub Security Advisories** (preferred) — open a private report via the
   ["Report a vulnerability"](https://github.com/masterPiece93/django-gauth/security/advisories/new)
   button on the repository's **Security** tab.
2. **Email** — contact the maintainer directly at **ankit8290@gmail.com** with the subject
   line `[django-gauth security]`.

### What to include

To help us triage quickly, please include as much of the following as possible:

- A description of the vulnerability and its potential impact.
- The affected version(s) of `django-gauth`.
- Step-by-step instructions to reproduce the issue.
- A proof-of-concept, if available.
- Any suggested mitigation or fix.

> ⚠️ **Never include real secrets** in your report — redact client IDs, client secrets,
> access/refresh tokens, and authorization codes. Use placeholders instead.

---

## What to Expect

- **Acknowledgement:** we aim to acknowledge your report within **5 business days**.
- **Assessment:** we will investigate and keep you informed of our progress.
- **Fix & disclosure:** once a fix is ready, we will coordinate a release and a responsible
  public disclosure. With your permission, we are happy to credit you for the discovery.

We ask that you give us a reasonable amount of time to address the issue before any public
disclosure.

---

## Scope

Reports that are **in scope** include, for example:

- Flaws in the OAuth2 authorization/callback flow (e.g. state/CSRF handling).
- Improper handling, storage, or exposure of credentials, tokens, or secrets.
- Authentication bypasses or session-fixation issues in the app's views/utilities.

The following are generally **out of scope**:

- Vulnerabilities in your own Django project configuration or deployment.
- Issues in third-party dependencies (please report those upstream — though we appreciate a
  heads-up so we can pin/upgrade).
- Reports requiring physical access or a compromised end-user device.

---

## Security Best Practices for Users

When using `django-gauth`, we strongly recommend:

- Always serve OAuth flows over **HTTPS** in production (never disable transport security
  outside local development).
- Keep `GOOGLE_CLIENT_SECRET` and other secrets out of version control (use environment
  variables or a secrets manager).
- `django-gauth` never persists your `client_id`/`client_secret` in the session store —
  they are re-injected from settings when rebuilding credentials — so use a secure session
  backend and signed/HTTPS-only cookies for the tokens that are stored.
- Keep `django-gauth`, Django, and `google-auth-oauthlib` up to date.
- Review the [documentation](https://masterpiece93.github.io/django-gauth/) for secure
  configuration guidance.

Thank you for practising responsible disclosure. 💙
