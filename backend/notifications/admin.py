from django.contrib import admin

from .models import NotificationEnvoyee


@admin.register(NotificationEnvoyee)
class NotificationEnvoyeeAdmin(admin.ModelAdmin):
    list_display = ("event", "cle_cible", "date_envoi")
    list_filter = ("event",)
    search_fields = ("event", "cle_cible")
    ordering = ("-date_envoi",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
