from django.contrib import admin

from .models import (
    BonTravail,
    BonTravailConsommable,
    BonTravailConsommableReservation,
    BonTravailDocument,
    CodeDefautOBD,
    DemandeIntervention,
    DemandeInterventionDocument,
    IncidentVehicule,
    PlanMaintenance,
    PlanMaintenanceConsommable,
    PlanMaintenanceDocument,
    Sinistre,
    TypePlanMaintenance,
)

# ==================== MIXINS (DRY) ====================


class ArchivableAdminMixin:
    """
    Mixin réutilisable pour les modèles possédant un champ 'archive'.
    Ajoute automatiquement le filtre et la colonne d'archivage.
    """

    def get_list_filter(self, request):
        base = list(super().get_list_filter(request))
        if "archive" not in base:
            base.append("archive")
        return base


# ==================== INLINES ====================


class BonTravailDocumentInline(admin.TabularInline):
    model = BonTravailDocument
    extra = 0


class BonTravailConsommableInline(admin.TabularInline):
    model = BonTravailConsommable
    extra = 0


class BonTravailConsommableReservationInline(admin.TabularInline):
    model = BonTravailConsommableReservation
    extra = 0


class DemandeInterventionDocumentInline(admin.TabularInline):
    model = DemandeInterventionDocument
    extra = 0


class PlanMaintenanceConsommableInline(admin.TabularInline):
    model = PlanMaintenanceConsommable
    extra = 0
    fields = ("consommable", "quantite_necessaire")


class PlanMaintenanceDocumentInline(admin.TabularInline):
    model = PlanMaintenanceDocument
    extra = 0


# ==================== MAINTENANCE CORRECTIVE ====================


@admin.register(DemandeIntervention)
class DemandeInterventionAdmin(ArchivableAdminMixin, admin.ModelAdmin):
    list_display = ("nom", "statut", "statut_suppose", "equipement", "utilisateur", "date_creation")
    list_filter = ("statut", "statut_suppose")
    search_fields = ("nom", "equipement__designation", "utilisateur__nomUtilisateur")
    readonly_fields = ("date_creation", "date_changementStatut")
    ordering = ("-date_creation",)
    inlines = [DemandeInterventionDocumentInline]
    date_hierarchy = "date_creation"
    list_per_page = 20
    list_select_related = ("equipement", "utilisateur")

    fieldsets = (
        ("Identification", {"fields": ("nom", "commentaire")}),
        ("Statut", {"fields": ("statut", "statut_suppose")}),
        ("Relations", {"fields": ("equipement", "utilisateur")}),
        ("Dates", {"fields": ("date_creation", "date_changementStatut"), "classes": ("collapse",)}),
        ("Administration", {"fields": ("archive",), "classes": ("collapse",)}),
    )


@admin.register(BonTravail)
class BonTravailAdmin(ArchivableAdminMixin, admin.ModelAdmin):
    list_display = ("nom", "type", "statut", "demande_intervention", "date_debut", "date_fin")
    list_filter = ("type", "statut")
    search_fields = (
        "nom",
        "demande_intervention__nom",
        "demande_intervention__equipement__designation",
    )
    readonly_fields = ("date_assignation",)
    ordering = ("-date_assignation",)
    inlines = [BonTravailDocumentInline, BonTravailConsommableInline]
    date_hierarchy = "date_assignation"
    list_per_page = 20
    list_select_related = ("demande_intervention",)

    fieldsets = (
        ("Identification", {"fields": ("nom", "type", "diagnostic", "commentaire")}),
        ("Statut", {"fields": ("statut", "commentaire_refus_cloture")}),
        (
            "Planification",
            {"fields": ("date_prevue", "duree_previsionnelle", "date_debut", "date_fin")},
        ),
        ("Relations", {"fields": ("demande_intervention", "responsable", "utilisateur_assigne")}),
        (
            "Pièces & clôture",
            {
                "fields": (
                    "pieces_recuperees",
                    "date_recuperation",
                    "date_cloture",
                    "date_assignation",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Administration", {"fields": ("archive",), "classes": ("collapse",)}),
    )


@admin.register(BonTravailConsommable)
class BonTravailConsommableAdmin(admin.ModelAdmin):
    list_display = ("bon_travail", "consommable", "quantite_utilisee")
    search_fields = ("bon_travail__nom", "consommable__designation")
    inlines = [BonTravailConsommableReservationInline]


# ==================== MAINTENANCE PRÉVENTIVE ====================


@admin.register(TypePlanMaintenance)
class TypePlanMaintenanceAdmin(admin.ModelAdmin):
    list_display = ("id", "libelle")
    search_fields = ("libelle",)
    ordering = ("libelle",)


@admin.register(PlanMaintenance)
class PlanMaintenanceAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "equipement",
        "type_plan_maintenance",
        "necessiteHabilitationElectrique",
        "necessitePermisFeu",
    )
    list_filter = ("type_plan_maintenance", "necessiteHabilitationElectrique", "necessitePermisFeu")
    search_fields = ("nom", "equipement__designation")
    ordering = ("nom",)
    inlines = [PlanMaintenanceConsommableInline, PlanMaintenanceDocumentInline]


# ==================== TABLES D'ASSOCIATION (lecture seule) ====================


@admin.register(BonTravailDocument)
class BonTravailDocumentAdmin(admin.ModelAdmin):
    list_display = ("bon_travail", "document")
    search_fields = ("bon_travail__nom", "document__nomDocument")


@admin.register(BonTravailConsommableReservation)
class BonTravailConsommableReservationAdmin(admin.ModelAdmin):
    list_display = ("bon_travail_consommable", "quantite", "magasin")
    search_fields = ("bon_travail_consommable__bon_travail__nom",)


@admin.register(PlanMaintenanceConsommable)
class PlanMaintenanceConsommableAdmin(admin.ModelAdmin):
    list_display = ("plan_maintenance", "consommable", "quantite_necessaire")
    search_fields = ("plan_maintenance__nom", "consommable__designation")


@admin.register(PlanMaintenanceDocument)
class PlanMaintenanceDocumentAdmin(admin.ModelAdmin):
    list_display = ("plan_maintenance", "document")
    search_fields = ("plan_maintenance__nom", "document__nomDocument")


@admin.register(DemandeInterventionDocument)
class DemandeInterventionDocumentAdmin(admin.ModelAdmin):
    list_display = ("demande_intervention", "document")
    search_fields = ("demande_intervention__nom", "document__nomDocument")


# ==================== FLOTTE : AVARIES & DIAGNOSTIC ====================


@admin.register(IncidentVehicule)
class IncidentVehiculeAdmin(admin.ModelAdmin):
    list_display = ("demande_intervention", "type_avarie", "gravite", "immobilisation")
    list_filter = ("type_avarie", "gravite", "immobilisation")
    search_fields = ("demande_intervention__nom", "demande_intervention__equipement__designation")


@admin.register(Sinistre)
class SinistreAdmin(admin.ModelAdmin):
    list_display = (
        "incident_vehicule",
        "date_accident",
        "lieu_accident",
        "numero_declaration_assurance",
    )
    search_fields = (
        "lieu_accident",
        "numero_declaration_assurance",
        "incident_vehicule__demande_intervention__nom",
    )
    ordering = ("-date_accident",)


@admin.register(CodeDefautOBD)
class CodeDefautOBDAdmin(admin.ModelAdmin):
    list_display = ("vehicule_profile", "code", "source", "date_lecture", "incident_vehicule")
    list_filter = ("source",)
    search_fields = ("code", "description", "vehicule_profile__equipement__designation")
    ordering = ("-date_lecture",)
