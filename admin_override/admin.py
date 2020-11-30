from allauth.account.models import EmailAddress
from django.contrib import admin


class EmailAddressAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False


admin.site.unregister(EmailAddress)
admin.site.register(EmailAddress, EmailAddressAdmin)
