from django.contrib import admin

from .models import (
    CarteGrise,
    Compteur,
    ControleTechnique,
    Declencher,
    DocumentEquipement,
    Equipement,
    FamilleEquipement,
    ModeleEquipement,
    StatutEquipement,
    VehiculeProfile,
)

# ==================== INLINES ====================


class CompteurInline(admin.TabularInline):
    """Compteurs associés à un équipement, affichés en ligne."""

    model = Compteur
    extra = 0
    fields = ("nomCompteur", "type", "valeurCourante", "unite", "estPrincipal")


class StatutEquipementInline(admin.TabularInline):
    """Historique des statuts d'un équipement, en lecture seule."""

    model = StatutEquipement
    extra = 0
    readonly_fields = ("statut", "dateChangement")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ==================== ÉQUIPEMENTS ====================


@admin.register(Equipement)
class EquipementAdmin(admin.ModelAdmin):
    list_display = ("designation", "numSerie", "lieu", "famille", "modele", "archive")
    list_filter = ("archive", "famille", "lieu")
    search_fields = ("designation", "numSerie", "reference")
    readonly_fields = ("dateCreation",)
    ordering = ("designation",)
    inlines = [CompteurInline, StatutEquipementInline]
    list_select_related = ("lieu", "famille", "modele")
    list_per_page = 25

    fieldsets = (
        ("Identification", {"fields": ("designation", "numSerie", "reference", "lienImage")}),
        ("Classification", {"fields": ("famille", "modele", "fabricant", "fournisseur")}),
        ("Localisation", {"fields": ("lieu", "x", "y")}),
        (
            "Informations financières",
            {
                "fields": ("prixAchat", "dateMiseEnService", "dateCreation"),
                "classes": ("collapse",),
            },
        ),
        ("Administration", {"fields": ("createurEquipement", "archive"), "classes": ("collapse",)}),
    )


@admin.register(Compteur)
class CompteurAdmin(admin.ModelAdmin):
    list_display = ("nomCompteur", "equipement", "type", "valeurCourante", "unite", "estPrincipal")
    list_filter = ("type", "estPrincipal")
    search_fields = ("nomCompteur", "equipement__designation")
    ordering = ("equipement__designation", "nomCompteur")


@admin.register(StatutEquipement)
class StatutEquipementAdmin(admin.ModelAdmin):
    list_display = ("statut", "equipement", "dateChangement")
    list_filter = ("statut",)
    search_fields = ("equipement__designation",)
    readonly_fields = ("dateChangement",)
    ordering = ("-dateChangement",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ==================== DONNÉES DE RÉFÉRENCE ====================


@admin.register(FamilleEquipement)
class FamilleEquipementAdmin(admin.ModelAdmin):
    list_display = ("nom", "familleParente")
    search_fields = ("nom",)
    ordering = ("nom",)


@admin.register(ModeleEquipement)
class ModeleEquipementAdmin(admin.ModelAdmin):
    list_display = ("nom", "fabricant")
    list_filter = ("fabricant",)
    search_fields = ("nom", "fabricant__nom")
    ordering = ("nom",)


@admin.register(Declencher)
class DeclencherAdmin(admin.ModelAdmin):
    list_display = (
        "compteur",
        "planMaintenance",
        "prochaineMaintenance",
        "derniereIntervention",
        "estGlissant",
    )
    list_filter = ("estGlissant",)
    search_fields = ("compteur__nomCompteur", "planMaintenance__nom")


@admin.register(DocumentEquipement)
class DocumentEquipementAdmin(admin.ModelAdmin):
    list_display = ("equipement", "document")
    search_fields = ("equipement__designation", "document__nomDocument")


# ==================== FLOTTE ====================


@admin.register(VehiculeProfile)
class VehiculeProfileAdmin(admin.ModelAdmin):
    list_display = ("immatriculation", "vin", "equipement", "genre", "energie")
    list_filter = ("genre", "energie")
    search_fields = ("immatriculation", "vin", "equipement__designation")
    ordering = ("immatriculation",)


@admin.register(CarteGrise)
class CarteGriseAdmin(admin.ModelAdmin):
    list_display = ("immatriculation", "titulaire", "vehicule_profile", "date_emission")
    search_fields = ("immatriculation", "titulaire", "vehicule_profile__equipement__designation")
    ordering = ("-date_emission",)


@admin.register(ControleTechnique)
class ControleTechniqueAdmin(admin.ModelAdmin):
    list_display = (
        "vehicule_profile",
        "resultat",
        "date_passage",
        "date_echeance",
        "centre_controle",
    )
    list_filter = ("resultat",)
    search_fields = (
        "vehicule_profile__equipement__designation",
        "vehicule_profile__immatriculation",
    )
    ordering = ("-date_passage",)
