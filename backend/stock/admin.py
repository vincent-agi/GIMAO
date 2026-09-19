from django.contrib import admin

from .models import Consommable, EstCompatible, Magasin, PorterSur, Stocker

# ==================== INLINES ====================


class StockerInline(admin.TabularInline):
    """Stock d'un consommable par magasin, affiché en ligne dans le consommable."""

    model = Stocker
    extra = 0
    fields = ("magasin", "quantite")


class PorterSurInline(admin.TabularInline):
    """Fournitures d'un consommable (fournisseur, fabricant, prix)."""

    model = PorterSur
    extra = 0
    fields = ("fournisseur", "fabricant", "quantite", "prix_unitaire", "date_reference_prix")


# ==================== STOCK ====================


@admin.register(Magasin)
class MagasinAdmin(admin.ModelAdmin):
    list_display = ("nom", "estMobile", "adresse", "archive")
    list_filter = ("estMobile", "archive")
    search_fields = ("nom",)
    ordering = ("nom",)


@admin.register(Consommable)
class ConsommableAdmin(admin.ModelAdmin):
    list_display = ("designation", "seuilStockFaible", "archive")
    list_filter = ("archive",)
    search_fields = ("designation",)
    ordering = ("designation",)
    inlines = [StockerInline, PorterSurInline]


@admin.register(Stocker)
class StockerAdmin(admin.ModelAdmin):
    list_display = ("consommable", "magasin", "quantite")
    list_filter = ("magasin",)
    search_fields = ("consommable__designation", "magasin__nom")
    ordering = ("magasin__nom", "consommable__designation")


@admin.register(EstCompatible)
class EstCompatibleAdmin(admin.ModelAdmin):
    list_display = ("consommable", "modeleEquipement")
    search_fields = ("consommable__designation", "modeleEquipement__nom")


@admin.register(PorterSur)
class PorterSurAdmin(admin.ModelAdmin):
    list_display = (
        "consommable",
        "fournisseur",
        "fabricant",
        "quantite",
        "prix_unitaire",
        "date_reference_prix",
    )
    list_filter = ("fournisseur", "fabricant")
    search_fields = ("consommable__designation", "fournisseur__nom", "fabricant__nom")
    ordering = ("-date_reference_prix",)
