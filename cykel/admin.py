from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CykelLogEntry, User

admin.site.site_header = "openbike"
admin.site.site_title = "openbike"
admin.site.index_title = "openbike configuration"


class CykelUserAdmin(UserAdmin):
    """Fork of UserAdmin, with all references to first_name, last_name and
    email removed."""

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("username", "is_staff")
    search_fields = ("username",)


admin.site.register(User, CykelUserAdmin)


@admin.register(CykelLogEntry)
class CykelLogEntryAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list_logentry.html"
    change_form_template = "admin/change_form_logentry.html"

    list_display_links = None
    list_display = (
        "timestamp",
        "content_type",
        "content_object",
        "action_type",
        "data",
    )

    def has_view_perission(self, request, obj=None):
        if request.user.has_perm("bikesharing.maintain"):
            return True
        return super().has_view_perission(self, request, obj=obj)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
