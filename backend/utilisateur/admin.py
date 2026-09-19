from django.contrib import admin, messages

from .models import Log, Module, Permission, Role, RolePermission, Utilisateur


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "permission":
            kwargs["queryset"] = Permission.objects.exclude(
                nomPermission__endswith=":export"
            ).exclude(nomPermission="export:view")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RoleAdmin(admin.ModelAdmin):
    list_display = ("nomRole",)
    search_fields = ("nomRole",)
    ordering = ("nomRole",)
    inlines = [RolePermissionInline]


class UtilisateurAdmin(admin.ModelAdmin):
    list_display = (
        "nomUtilisateur",
        "prenom",
        "nomFamille",
        "email",
        "role",
        "actif",
        "a_mot_de_passe",
        "derniereConnexion",
    )
    list_filter = ("actif", "role", "dateCreation")
    search_fields = ("nomUtilisateur", "prenom", "nomFamille", "email")
    readonly_fields = ("dateCreation", "derniereConnexion", "a_mot_de_passe")
    ordering = ("nomFamille", "prenom")
    list_select_related = ("role",)
    list_per_page = 25

    fieldsets = (
        ("Informations de connexion", {"fields": ("nomUtilisateur", "email", "role")}),
        ("Informations personnelles", {"fields": ("prenom", "nomFamille")}),
        (
            "Statut du compte",
            {"fields": ("actif", "a_mot_de_passe", "derniereConnexion", "dateCreation")},
        ),
    )

    add_fieldsets = (
        ("Informations de connexion", {"fields": ("nomUtilisateur", "email", "role")}),
        ("Informations personnelles", {"fields": ("prenom", "nomFamille")}),
        ("Statut du compte", {"fields": ("actif",)}),
    )

    def a_mot_de_passe(self, obj):
        """Indique si l'utilisateur a défini un mot de passe"""
        return obj.has_usable_password()

    a_mot_de_passe.boolean = True
    a_mot_de_passe.short_description = "Mot de passe défini"

    def save_model(self, request, obj, form, change):
        """
        Surcharge pour créer des utilisateurs SANS mot de passe.
        L'utilisateur devra le définir à sa première connexion.
        """
        if not change:  # Si c'est une création
            # Ne définit PAS de mot de passe, laisse à None
            obj.motDePasse = None

            # Sauvegarde l'utilisateur
            super().save_model(request, obj, form, change)

            # Message d'information
            messages.success(
                request,
                f"Utilisateur '{obj.nomUtilisateur}' créé avec succès ! "
                f"L'utilisateur devra définir son mot de passe lors de sa première connexion.",
            )
        else:
            # Si c'est une modification, sauvegarde normalement
            super().save_model(request, obj, form, change)

    def get_fieldsets(self, request, obj=None):
        """
        Retourne des fieldsets différents pour la création et la modification
        """
        if not obj:  # Si c'est une création
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)


class LogAdmin(admin.ModelAdmin):
    list_display = ("type", "nomTable", "date", "utilisateur")
    list_filter = ("type", "nomTable")
    search_fields = ("type", "nomTable", "utilisateur__nomUtilisateur")
    readonly_fields = ("type", "nomTable", "idCible", "champsModifies", "date", "utilisateur")
    ordering = ("-date",)
    date_hierarchy = "date"
    list_per_page = 25
    list_select_related = ("utilisateur",)
    # Le COUNT(*) sur une grande table de logs est coûteux : on le désactive
    show_full_result_count = False

    def has_add_permission(self, request):
        """Les logs ne peuvent pas être créés manuellement"""
        return False

    def has_change_permission(self, request, obj=None):
        """Les logs ne peuvent pas être modifiés"""
        return False


class ModuleAdmin(admin.ModelAdmin):
    list_display = ("code", "nom")
    search_fields = ("code", "nom")
    ordering = ("nom",)


class PermissionAdmin(admin.ModelAdmin):
    list_display = ("get_label", "nomPermission", "module", "description")
    search_fields = ("nomPermission",)
    list_filter = ("module",)
    ordering = ("module__nom", "nomPermission")

    list_select_related = ("module",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .exclude(nomPermission__endswith=":export")
            .exclude(nomPermission="export:view")
        )

    def get_label(self, obj):
        FULL_LABELS = {
            "di:viewList": "Voir la liste des DI",
            "di:viewDetail": "Voir le détail d'une DI",
            "di:create": "Créer une DI",
            "di:editCreated": "Modifier ses propres DI",
            "di:editAll": "Modifier toutes les DI",
            "di:delete": "Supprimer une DI",
            "di:accept": "Accepter une DI",
            "di:refuse": "Refuser une DI",
            "di:transform": "Transformer une DI en BT",
            "bt:viewList": "Voir la liste des BT",
            "bt:viewDetail": "Voir le détail d'un BT",
            "bt:create": "Créer un BT",
            "bt:editAll": "Modifier tous les BT",
            "bt:editAssigned": "Modifier ses BT assignés",
            "bt:delete": "Supprimer un BT",
            "bt:start": "Démarrer un BT",
            "bt:end": "Clôturer un BT",
            "bt:refuse": "Refuser un BT",
            "bt:refuseClosure": "Refuser la clôture d'un BT",
            "bt:acceptClosure": "Accepter la clôture d'un BT",
            "bt:acceptConsumableRequest": "Valider une demande de consommable",
            "eq:viewList": "Voir la liste des équipements",
            "eq:viewDetail": "Voir le détail d'un équipement",
            "eq:create": "Créer un équipement",
            "eq:edit": "Modifier un équipement",
            "eq:delete": "Supprimer un équipement",
            "cp:viewList": "Voir la liste des compteurs",
            "cp:viewDetail": "Voir le détail d'un compteur",
            "cp:create": "Créer un compteur",
            "cp:edit": "Modifier un compteur",
            "cp:delete": "Supprimer un compteur",
            "mp:viewList": "Voir la liste des maintenances préventives",
            "mp:viewDetail": "Voir le détail d'une maintenance préventive",
            "mp:create": "Créer une maintenance préventive",
            "mp:edit": "Modifier une maintenance préventive",
            "mp:delete": "Supprimer une maintenance préventive",
            "stock:view": "Voir les stocks",
            "cons:viewDetail": "Voir le détail d'un consommable",
            "cons:create": "Créer un consommable",
            "cons:edit": "Modifier un consommable",
            "cons:delete": "Supprimer un consommable",
            "mag:viewList": "Voir la liste des magasins",
            "mag:viewDetail": "Voir le détail d'un magasin",
            "mag:create": "Créer un magasin",
            "mag:edit": "Modifier un magasin",
            "mag:delete": "Supprimer un magasin",
            "user:viewList": "Voir la liste des utilisateurs",
            "user:viewDetail": "Voir le détail d'un utilisateur",
            "user:create": "Créer un utilisateur",
            "user:edit": "Modifier un utilisateur",
            "user:disable": "Désactiver un utilisateur",
            "user:enable": "Activer un utilisateur",
            "user:delete": "Supprimer un utilisateur",
            "role:viewList": "Voir la liste des rôles",
            "role:viewDetail": "Voir le détail d'un rôle",
            "role:create": "Créer un rôle",
            "role:edit": "Modifier un rôle",
            "role:delete": "Supprimer un rôle",
            "loc:viewList": "Voir la liste des lieux",
            "loc:viewDetail": "Voir le détail d'un lieu",
            "loc:create": "Créer un lieu",
            "loc:edit": "Modifier un lieu",
            "loc:delete": "Supprimer un lieu",
            "sup:viewList": "Voir la liste des fournisseurs",
            "sup:viewDetail": "Voir le détail d'un fournisseur",
            "sup:create": "Créer un fournisseur",
            "sup:edit": "Modifier un fournisseur",
            "sup:delete": "Supprimer un fournisseur",
            "man:viewList": "Voir la liste des fabricants",
            "man:viewDetail": "Voir le détail d'un fabricant",
            "man:create": "Créer un fabricant",
            "man:edit": "Modifier un fabricant",
            "man:delete": "Supprimer un fabricant",
            "eqmod:viewList": "Voir la liste des modèles d'équipement",
            "eqmod:viewDetail": "Voir le détail d'un modèle d'équipement",
            "eqmod:create": "Créer un modèle d'équipement",
            "eqmod:edit": "Modifier un modèle d'équipement",
            "eqmod:delete": "Supprimer un modèle d'équipement",
            "menu:view": "Accéder au menu de navigation",
            "menu:dataManagement": "Accéder au menu Gestion des données",
            "dash:display.bt": "Afficher les BT sur le dashboard",
            "dash:display.btAssigned": "Afficher ses BT assignés sur le dashboard",
            "dash:display.di": "Afficher les DI sur le dashboard",
            "dash:display.diCreated": "Afficher ses DI créées sur le dashboard",
            "dash:display.eq": "Afficher les équipements sur le dashboard",
            "dash:display.mag": "Afficher les magasins sur le dashboard",
            "dash:display.vertical": "Afficher le dashboard en mode vertical",
            "dash:stats.bt": "Voir les statistiques de ses BT",
            "dash:stats.di": "Voir les statistiques de ses DI",
            "dash:stats.full": "Voir toutes les statistiques",
        }
        return FULL_LABELS.get(obj.nomPermission, obj.nomPermission)

    get_label.short_description = "Label lisible"


class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission")
    list_filter = ("role",)
    search_fields = ("role__nomRole", "permission__nomPermission")
    ordering = ("role", "permission")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "permission":
            kwargs["queryset"] = Permission.objects.exclude(
                nomPermission__endswith=":export"
            ).exclude(nomPermission="export:view")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Module, ModuleAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(RolePermission, RolePermissionAdmin)
