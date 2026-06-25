---
title: UI Customization
description: Customize the Django Gauth landing page appearance.
tags:
  - configuration
  - ui
  - theming
---

# UI Customization :material-palette:

Django Gauth ships with a built-in landing page. You can customize its appearance via settings.

---

## Default Appearance

Out of the box, the landing page has:

- A purple navbar (`#4b286d`)
- White text
- A default logo
- A placeholder profile image

---

## Customizing with `DJANGO_GAUTH_UI_CONFIG`

Add this to your `settings.py`:

```python title="settings.py"
DJANGO_GAUTH_UI_CONFIG = {
    "index": {
        "navbar": {
            "logo": "https://your-cdn.com/your-logo.png",
            "profile_picture_absence": "https://your-cdn.com/default-avatar.png",
        }
    }
}
```

### Configuration Options

| Key | Description | Default |
|-----|-------------|---------|
| `index.navbar.logo` | URL to your organization's logo | Built-in logo |
| `index.navbar.profile_picture_absence` | Placeholder when no profile pic | Built-in placeholder |

---

## Default Theme Values

These are applied automatically to the template context:

```python
{
    "default_index_navbar_background": "#4b286d",      # Navbar background color
    "default_index_navbar_text_color": "white",        # Navbar text color
    "default_index_navbar_logo_background": "inherit", # Logo background
}
```

---

## Static Files Considerations

!!! info "Hosted URLs vs Static Files"
    If you provide **hosted URLs** (CDN, S3, etc.) for logo and placeholder, you don't need to manage static files for Django Gauth.

    If you rely on the **default built-in assets**, you need Django's static files working:

    ```bash
    python manage.py collectstatic
    ```

See the [Production Guide](../guides/production.md) for static file deployment details.
