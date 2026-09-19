from django.contrib import admin

from .models import ApiToken


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "valid_until", "is_revoked", "token_preview")
    list_filter = ("is_revoked",)
    search_fields = ("user__nomUtilisateur", "user__email")
    readonly_fields = ("token_hash", "created_at")
    ordering = ("-created_at",)

    @admin.display(description="Token (aperçu)")
    def token_preview(self, obj):
        """Affiche seulement les 10 premiers caractères du hash pour la sécurité."""
        return f"{obj.token_hash[:10]}…"

    def has_add_permission(self, request):
        """Les tokens sont générés programmatiquement, pas via l'admin."""
        return False
