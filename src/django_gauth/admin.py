from django.contrib import admin
from django.contrib.sessions.models import Session

# Register your models here.


class SessionAdmin(admin.ModelAdmin):
    list_display = ["session_key", "_session_data", "expire_date"]
    readonly_fields = ["_session_data"]
    exclude = [
        "session_data"
    ]  # This line ensures that encoded session in not shown . Comment this if you want to see the encoded session data as well .

    def _session_data(self, obj):
        import pprint

        return pprint.pformat(obj.get_decoded()).replace("\n", "<br>\n")

    _session_data.allow_tags = True


admin.site.register(Session, SessionAdmin)
