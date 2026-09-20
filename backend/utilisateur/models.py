from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Role(models.Model):
    """
    Représente un rôle attribué à un utilisateur
    """

    nomRole = models.CharField(
        max_length=50, help_text="Nom du rôle (ex: Administrateur, Technicien, etc.)"
    )
    estDefaut = models.BooleanField(default=False, help_text="Rôle par défaut non supprimable")
    # rang = models.PositiveSmallIntegerField(
    #     help_text="Rang du rôle pour hiérarchiser les permissions (plus petit = plus élevé)"
    # )
    permissions = models.ManyToManyField(
        "Permission",
        through="RolePermission",
        related_name="roles",
        help_text="Permissions associées à ce rôle",
    )

    class Meta:
        db_table = "gimao_role"
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        indexes = [
            models.Index(fields=["nomRole"], name="role_nom_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.nomRole}"

        # ordering = ['rang']


class Utilisateur(models.Model):
    """
    Représente un utilisateur du système.
    """

    nomUtilisateur = models.CharField(
        max_length=50, unique=True, help_text="Identifiant unique pour la connexion"
    )
    motDePasse = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Mot de passe hashé de l'utilisateur (null si pas encore défini)",
    )
    prenom = models.CharField(max_length=50, help_text="Prénom de l'utilisateur")
    nomFamille = models.CharField(max_length=50, help_text="Nom de famille de l'utilisateur")
    email = models.EmailField(
        max_length=150, unique=True, help_text="Adresse email de l'utilisateur"
    )
    photoProfil = models.FileField(
        upload_to="utilisateur_photos/",
        null=True,
        blank=True,
        help_text="Photo de profil de l'utilisateur",
    )
    derniereConnexion = models.DateTimeField(
        null=True, blank=True, help_text="Date et heure de la dernière connexion"
    )
    dateCreation = models.DateTimeField(auto_now_add=True, help_text="Date de création du compte")
    actif = models.BooleanField(default=True, help_text="Indique si le compte est actif")
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="utilisateurs",
        help_text="Rôle attribué à l'utilisateur",
    )

    class Meta:
        db_table = "gimao_utilisateur"
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["nomFamille", "prenom"]
        indexes = [
            models.Index(fields=["nomFamille", "prenom", "id"], name="user_name_list_idx"),
            models.Index(fields=["role", "nomFamille", "prenom", "id"], name="user_role_list_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.nomUtilisateur} - {self.prenom} {self.nomFamille}"

    def save(self, *args, **kwargs):
        old_file = None
        if self.pk:
            try:
                old = Utilisateur.objects.only("photoProfil").get(pk=self.pk)
                old_file = old.photoProfil if old and old.photoProfil else None
            except Utilisateur.DoesNotExist:
                old_file = None

        super().save(*args, **kwargs)

        # Si la photo a été remplacée ou supprimée, on supprime l'ancien fichier.
        try:
            current_name = self.photoProfil.name if self.photoProfil else ""
            old_name = old_file.name if old_file else ""
            if old_name and old_name != current_name:
                old_file.delete(save=False)
        except Exception:
            # Ne pas casser une sauvegarde d'utilisateur si le fichier n'est plus présent.
            pass

    def delete(self, *args, **kwargs):
        file_to_delete = self.photoProfil if self.photoProfil else None
        super().delete(*args, **kwargs)
        try:
            if file_to_delete and file_to_delete.name:
                file_to_delete.delete(save=False)
        except Exception:
            pass

    def get_full_name(self):
        return f"{self.prenom} {self.nomFamille}"

    def set_password(self, raw_password):
        if raw_password:
            self.motDePasse = make_password(raw_password)
        else:
            self.motDePasse = None

    def check_password(self, raw_password):
        if not self.motDePasse:
            return False
        return check_password(raw_password, self.motDePasse)

    def has_usable_password(self):
        return self.motDePasse is not None and self.motDePasse != ""

    def premiere_connexion(self):
        return self.derniereConnexion is None


class Log(models.Model):
    """
    Représente un journal d'activité ou de modification dans le système.
    """

    type = models.CharField(
        max_length=50, help_text="Type de log (ex: création, modification, suppression)"
    )
    nomTable = models.CharField(max_length=50, help_text="Nom de la table affectée par l'action")
    idCible = models.JSONField(help_text="Identifiant(s) de l'objet modifié")
    champsModifies = models.JSONField(help_text="Champs modifiés et leurs nouvelles valeurs")
    date = models.DateTimeField(auto_now_add=True, help_text="Date et heure de l'action")
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
        help_text="Utilisateur qui a effectué l'action",
    )
    group = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
        help_text="Identifiant unique du groupe de logs (lié à une requête)",
    )

    class Meta:
        db_table = "gimao_log"
        verbose_name = "Log"
        verbose_name_plural = "Logs"
        ordering = ["-date"]
        indexes = [
            # Tri par date descendant (consultation par défaut)
            models.Index(fields=["-date"], name="log_date_desc_idx"),
            # Filtrage par utilisateur + date (logs d'un utilisateur)
            models.Index(fields=["utilisateur", "-date"], name="log_user_date_idx"),
            # Filtrage par table cible (ex : toutes les modifications sur BT)
            models.Index(fields=["nomTable", "-date"], name="log_table_date_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.nomTable} - action : {self.type} - {self.date}"


class Module(models.Model):
    """
    Représente un module fonctionnel regroupant des permissions (ex: di, bt, eq).
    """

    code = models.CharField(
        max_length=20, unique=True, help_text="Code court du module (ex: di, bt, eq)"
    )
    nom = models.CharField(
        max_length=100, help_text="Nom lisible du module (ex: Demandes d'intervention)"
    )

    class Meta:
        db_table = "gimao_module"
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Permission(models.Model):
    """
    Représente une permission spécifique attribuée à un rôle.
    """

    TYPE_AFFICHAGE = "affichage"
    TYPE_ACTION = "action"
    TYPE_CHOICES = [
        (TYPE_AFFICHAGE, "Affichage"),
        (TYPE_ACTION, "Action"),
    ]

    nomPermission = models.CharField(
        max_length=100,
        help_text="Nom de la permission (ex: ajouter_utilisateur, supprimer_equipement)",
        unique=True,
    )

    description = models.TextField(
        null=True, blank=True, help_text="Description détaillée de la permission"
    )

    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default=TYPE_ACTION,
        help_text="Type de permission : affichage (lecture) ou action (écriture)",
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enfants",
        help_text="Permission prérequise : cocher cette permission coche aussi son parent",
    )

    module = models.ForeignKey(
        "Module",
        on_delete=models.PROTECT,
        related_name="permissions",
        null=True,
        blank=True,
        help_text="Module auquel appartient cette permission",
    )

    class Meta:
        db_table = "gimao_permission"
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
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
            "veh:viewList": "Voir la liste des véhicules",
            "veh:viewDetail": "Voir le détail d'un véhicule",
            "veh:create": "Créer un véhicule",
            "veh:edit": "Modifier un véhicule",
            "veh:delete": "Supprimer un véhicule",
            "incident:viewList": "Voir la liste des incidents véhicule",
            "incident:viewDetail": "Voir le détail d'un incident véhicule",
            "incident:create": "Signaler un incident véhicule",
            "incident:edit": "Modifier un incident véhicule",
            "sinistre:viewList": "Voir la liste des sinistres",
            "sinistre:viewDetail": "Voir le détail d'un sinistre",
            "sinistre:create": "Déclarer un sinistre",
            "obd:viewList": "Voir la liste des codes défaut OBD",
            "obd:viewDetail": "Voir le détail d'un code défaut OBD",
            "obd:create": "Saisir un code défaut OBD",
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
        return f"{self.id} - {self.nomPermission} - {FULL_LABELS.get(self.nomPermission, self.nomPermission)}"


class RolePermission(models.Model):
    """
    Modèle intermédiaire pour lier les rôles aux permissions < autoriser >.
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
        help_text="Rôle auquel la permission est attribuée",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="permission_roles",
        help_text="Permission attribuée au rôle",
    )

    class Meta:
        db_table = "gimao_role_permission"
        verbose_name = "Rôle-Permission"
        verbose_name_plural = "Rôles-Permissions"
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.id} - {self.role.nomRole} - {self.permission.nomPermission}"


#  utilisateur permission


class UtilisateurPermission(models.Model):
    """
    Représente une permission spécifique attribuée à un rôle ou un utilisateur.

    Convention de nommage : <module>:<action>

    Modules disponibles :
        di      Demande d'Intervention
        bt      Bon de Travail
        eq      Équipement
        cp      Compteur
        mp      Maintenance Préventive
        stock   Stock
        cons    Consommable
        mag     Magasin
        user    Utilisateur
        role    Rôle
        loc     Lieu
        sup     Fournisseur (Supplier)
        man     Fabricant (Manufacturer)
        eqmod   Modèle d'équipement
        export  Export global
        menu    Accès au menu
        dash    Dashboard

    Actions disponibles :
        viewList        Voir la liste
        viewDetail      Voir le détail
        create          Créer
        edit            Modifier
        editAll         Modifier tous les enregistrements
        editCreated     Modifier ses propres enregistrements
        editAssigned    Modifier les enregistrements assignés
        delete          Supprimer
        export          Exporter
        accept          Accepter
        refuse          Refuser
        transform       Transformer en BT
        start           Démarrer
        end             Clôturer
        disable         Désactiver
        enable          Activer

    Exemples : di:create, bt:editAssigned, user:disable
    """

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="permissions_personnalisees",
        help_text="Utilisateur concerné",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="utilisateur_permissions",
        help_text="Permission accordée à l'utilisateur",
    )

    class Meta:
        db_table = "gimao_utilisateur_permission"
        verbose_name = "Permission utilisateur"
        verbose_name_plural = "Permissions utilisateur"
        unique_together = ("utilisateur", "permission")

    def __str__(self):
        return f"{self.id} - {self.utilisateur.nomUtilisateur} - {self.permission.nomPermission}"
