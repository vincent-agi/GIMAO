from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from donnees.models import Document
from equipement.models import Equipement
from gimao.mixins import ArchivableMixin
from stock.models import Consommable
from utilisateur.models import Utilisateur


class DemandeIntervention(ArchivableMixin, models.Model):
    """
    Demande d'intervention signalant une anomalie sur un équipement.

    Cycle de vie du statut :
        EN_ATTENTE → ACCEPTEE → TRANSFORMEE (création d'un BT)
        EN_ATTENTE → REFUSEE

    ``statut_suppose`` reflète l'état de l'équipement tel que perçu par l'opérateur
    au moment de la déclaration (peut différer du statut officiel de l'équipement).
    ``date_changementStatut`` est mis à jour à chaque transition de statut.
    """

    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("ACCEPTEE", "Acceptée"),
        ("REFUSEE", "Refusée"),
        ("TRANSFORMEE", "Transformée"),
    ]

    STATUTS_EQUIPEMENT_CHOICES = [
        ("EN_FONCTIONNEMENT", "En fonctionnement"),
        ("DEGRADE", "Dégradé"),
        ("A_LARRET", "A l'arrêt"),
        ("HORS_SERVICE", "Hors service"),
    ]

    commentaire = models.TextField(blank=True, null=True)
    nom = models.CharField(max_length=255)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES)
    statut_suppose = models.CharField(
        max_length=50, choices=STATUTS_EQUIPEMENT_CHOICES, default="EN_FONCTIONNEMENT"
    )
    date_creation = models.DateTimeField()
    date_changementStatut = models.DateTimeField()

    # Relations
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="demandes_intervention"
    )
    equipement = models.ForeignKey(
        Equipement, on_delete=models.CASCADE, related_name="demandes_intervention"
    )
    documents = models.ManyToManyField(
        Document,
        through="DemandeInterventionDocument",
        related_name="demandes_intervention",
        blank=True,
    )

    class Meta:
        db_table = "gimao_demande_intervention"
        verbose_name = "Demande d'intervention"
        verbose_name_plural = "Demandes d'intervention"
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["archive", "date_creation", "id"], name="di_arch_date_id_idx"),
            models.Index(
                fields=["archive", "equipement", "date_creation", "id"], name="di_arch_eq_date_idx"
            ),
            models.Index(
                fields=["archive", "utilisateur", "date_creation", "id"],
                name="di_arch_user_date_idx",
            ),
        ]

    def __str__(self):
        try:
            return f"{self.id} - {self.nom} - {self.equipement}"
        except Equipement.DoesNotExist:
            return f"{self.id} - {self.nom} - Équipement supprimé (id={self.equipement_id})"


class BonTravail(ArchivableMixin, models.Model):
    """
    Bon de travail généré suite à l'acceptation d'une demande d'intervention.

    Cycle de vie du statut :
        EN_ATTENTE → EN_COURS → TERMINE → CLOTURE
        EN_ATTENTE ou EN_COURS → EN_RETARD (géré automatiquement par le cron ``update_bt_status``)

    ``utilisateur_assigne`` est un M2M : plusieurs techniciens peuvent être affectés au même BT.
    ``responsable`` est le gestionnaire GMAO qui a validé la clôture.
    ``pieces_recuperees`` / ``date_recuperation`` tracent la restitution des consommables
    lorsque l'intervention n'a finalement pas eu lieu.
    ``commentaire_refus_cloture`` est renseigné si le responsable refuse la clôture demandée.
    """

    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("EN_COURS", "En cours"),
        ("TERMINE", "Terminé"),
        ("EN_RETARD", "En retard"),
        ("CLOTURE", "Clôturé"),
    ]

    TYPE_CHOICES = [("CORRECTIF", "Correctif"), ("PREVENTIF", "Préventif")]

    nom = models.CharField(max_length=255)
    diagnostic = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    date_assignation = models.DateTimeField(blank=True, null=True)
    date_cloture = models.DateTimeField(blank=True, null=True)
    date_debut = models.DateTimeField(blank=True, null=True)
    date_fin = models.DateTimeField(blank=True, null=True)
    date_prevue = models.DateTimeField(blank=True, null=True)
    duree_previsionnelle = models.DurationField(blank=True, null=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default="EN_ATTENTE")
    commentaire = models.TextField(blank=True, null=True)
    commentaire_refus_cloture = models.TextField(blank=True, null=True)

    pieces_recuperees = models.BooleanField(
        default=False, help_text="Indique si toutes les pieces ont ete recuperees pour ce BT"
    )
    date_recuperation = models.DateTimeField(
        blank=True, null=True, help_text="Date a laquelle les pieces ont ete recuperees"
    )

    # Relations
    demande_intervention = models.ForeignKey(
        DemandeIntervention, on_delete=models.CASCADE, related_name="bons_travail"
    )
    utilisateur_assigne = models.ManyToManyField(
        Utilisateur, blank=True, related_name="bons_travail_assignes"
    )
    responsable = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bons_travail_responsable",
    )
    consommables = models.ManyToManyField(
        Consommable, through="BonTravailConsommable", related_name="bons_travail", blank=True
    )
    documents = models.ManyToManyField(
        Document, through="BonTravailDocument", related_name="bons_travail", blank=True
    )

    class Meta:
        db_table = "gimao_bon_travail"
        verbose_name = "Bon de travail"
        verbose_name_plural = "Bons de travail"
        indexes = [
            models.Index(fields=["archive", "date_assignation", "id"], name="bt_arch_assign_idx"),
            models.Index(
                fields=["archive", "statut", "date_assignation", "id"], name="bt_arch_statut_idx"
            ),
        ]

    def __str__(self):
        return f"{self.id} - {self.nom} - {self.statut}"


class TypePlanMaintenance(models.Model):
    """Type de plan de maintenance (préventif, prédictif, etc.)"""

    libelle = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "gimao_type_plan_maintenance"
        verbose_name = "Type de plan de maintenance"
        verbose_name_plural = "Types de plan de maintenance"

    def __str__(self):
        return f"{self.id} - {self.libelle}"


class PlanMaintenance(models.Model):
    """Plan de maintenance pour un équipement"""

    nom = models.CharField(max_length=255)
    commentaire = models.TextField(blank=True, null=True)

    necessiteHabilitationElectrique = models.BooleanField(
        default=False, help_text="Nécessite une habilitation électrique"
    )
    necessitePermisFeu = models.BooleanField(default=False, help_text="Nécessite un permis feu")

    # Relations
    type_plan_maintenance = models.ForeignKey(
        TypePlanMaintenance, on_delete=models.CASCADE, related_name="plans_maintenance"
    )
    equipement = models.ForeignKey(
        Equipement, on_delete=models.CASCADE, related_name="plans_maintenance"
    )

    # Relations Many-to-Many
    documents = models.ManyToManyField(
        Document, through="PlanMaintenanceDocument", related_name="plans_maintenance", blank=True
    )
    consommables = models.ManyToManyField(
        Consommable,
        through="PlanMaintenanceConsommable",
        related_name="plans_maintenance",
        blank=True,
    )

    class Meta:
        db_table = "gimao_plan_maintenance"
        verbose_name = "Plan de maintenance"
        verbose_name_plural = "Plans de maintenance"

    def __str__(self):
        return f"{self.id} - {self.nom} - {self.equipement}"


# ==================== TABLE D'ASSOCIATION ====================


class PlanMaintenanceConsommable(models.Model):
    """Table d'association entre PlanMaintenance et Consommable"""

    plan_maintenance = models.ForeignKey(PlanMaintenance, on_delete=models.PROTECT)
    consommable = models.ForeignKey(Consommable, on_delete=models.CASCADE)
    quantite_necessaire = models.IntegerField(
        validators=[MinValueValidator(1)], default=1, help_text="Quantité nécessaire pour ce plan"
    )

    class Meta:
        db_table = "gimao_plan_maintenance_consommable"
        unique_together = ["plan_maintenance", "consommable"]
        verbose_name = "Consommable nécessaire"
        verbose_name_plural = "Consommables nécessaires"

    def __str__(self):
        return f"{self.id} - {self.plan_maintenance.nom} - Consommable {self.consommable.designation} (x{self.quantite_necessaire})"


class PlanMaintenanceDocument(models.Model):
    """Table d'association entre PlanMaintenance et Document"""

    plan_maintenance = models.ForeignKey(PlanMaintenance, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

    class Meta:
        db_table = "gimao_plan_maintenance_document"
        unique_together = ["plan_maintenance", "document"]
        verbose_name = "Document de plan de maintenance"
        verbose_name_plural = "Documents de plans de maintenance"

    def __str__(self):
        return f"{self.id} - {self.plan_maintenance.nom} - Document {self.document.nomDocument}"


class DemandeInterventionDocument(models.Model):
    """Table d'association entre DemandeIntervention et Document"""

    demande_intervention = models.ForeignKey(DemandeIntervention, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

    class Meta:
        db_table = "gimao_demande_intervention_document"
        unique_together = ["demande_intervention", "document"]
        verbose_name = "Document de demande d'intervention"
        verbose_name_plural = "Documents de demandes d'intervention"

    def __str__(self):
        return f"{self.id} - {self.demande_intervention.nom} - Document {self.document.nomDocument}"


class BonTravailDocument(models.Model):
    """Table d'association entre BonTravail et Document"""

    bon_travail = models.ForeignKey(BonTravail, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

    class Meta:
        db_table = "gimao_bon_travail_document"
        unique_together = ["bon_travail", "document"]
        verbose_name = "Document de bon de travail"
        verbose_name_plural = "Documents de bons de travail"

    def __str__(self):
        return f"{self.id} - {self.bon_travail.nom} - Document {self.document.nomDocument}"


class BonTravailConsommable(models.Model):
    """Table d'association entre BonTravail et Consommable"""

    bon_travail = models.ForeignKey(BonTravail, on_delete=models.CASCADE)
    consommable = models.ForeignKey(Consommable, on_delete=models.CASCADE)
    quantite_utilisee = models.IntegerField(
        validators=[MinValueValidator(0)], default=0, help_text="Quantité utilisée pour ce bon"
    )
    estConfirme = models.BooleanField(
        default=False, help_text="Indique si le consommable a été donné"
    )
    date_confirme = models.DateTimeField(
        blank=True, null=True, help_text="Date à laquelle le consommable a été distribué"
    )
    magasin_reserve = models.ForeignKey(
        "stock.Magasin",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Magasin d ou le consommable a ete mis de cote",
    )

    class Meta:
        db_table = "gimao_bon_travail_consommable"
        unique_together = ["bon_travail", "consommable"]
        verbose_name = "Consommable utilisé"
        verbose_name_plural = "Consommables utilisés"
        indexes = [
            models.Index(fields=["bon_travail", "estConfirme"], name="bt_conso_conf_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.bon_travail.nom} - {self.consommable.designation} (x{self.quantite_utilisee})"


class BonTravailConsommableReservation(models.Model):
    """Repartition d'un consommable de BT sur un ou plusieurs magasins."""

    bon_travail_consommable = models.ForeignKey(
        BonTravailConsommable, on_delete=models.CASCADE, related_name="reservations"
    )
    magasin = models.ForeignKey(
        "stock.Magasin", on_delete=models.CASCADE, related_name="reservations_bt"
    )
    quantite = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantite reservee dans ce magasin pour ce consommable",
    )

    class Meta:
        db_table = "gimao_bon_travail_consommable_reservation"
        unique_together = ["bon_travail_consommable", "magasin"]
        verbose_name = "Reservation de consommable"
        verbose_name_plural = "Reservations de consommables"

    def __str__(self):
        return f"{self.id} - {self.bon_travail_consommable.bon_travail.nom} - Reservation {self.magasin.nom} (x{self.quantite})"


class IncidentVehicule(models.Model):
    """
    Profil véhicule d'une DemandeIntervention, en relation un-à-un.

    Porte les métadonnées spécifiques à un incident/avarie véhicule (type
    d'avarie, gravité, immobilisation) sans polluer ``DemandeIntervention``,
    qui reste le socle générique de signalement d'anomalie pour tout type
    d'équipement (cf. ADR-001, TUS-020 — même pattern que ``VehiculeProfile``
    sur ``Equipement``).

    Un ``IncidentVehicule`` n'a de sens que si la ``DemandeIntervention``
    porte sur un équipement de type ``VEHICULE`` ; ce n'est pas imposé au
    niveau base de données (la DI reste générique), mais au niveau service
    (cf. TUS-020, à charge de l'appelant de ne créer ce profil que dans ce cas).

    Attributes:
        demande_intervention: La ``DemandeIntervention`` générique dont ce
            profil complète les données véhicule. Clé primaire du profil
            (relation 1-1 stricte).
        type_avarie: Nature de l'avarie signalée.
        gravite: Niveau de gravité perçu par le déclarant.
        immobilisation: Indique si le véhicule est immobilisé suite à cet
            incident (ne peut plus être utilisé en l'état).
    """

    TYPE_AVARIE_CHOICES = [
        ("VOYANT", "Voyant tableau de bord"),
        ("BRUIT_ANORMAL", "Bruit anormal"),
        ("ACCIDENT_ROUTE", "Accident de la route"),
        ("CODE_DEFAUT", "Code défaut"),
        ("USURE_SIGNALEE", "Usure signalée"),
        ("AUTRE", "Autre"),
    ]

    GRAVITE_CHOICES = [
        ("MINEURE", "Mineure"),
        ("MODEREE", "Modérée"),
        ("CRITIQUE", "Critique"),
    ]

    demande_intervention = models.OneToOneField(
        DemandeIntervention,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="incident_vehicule",
        help_text="Demande d'intervention générique dont ce profil complète les données véhicule",
    )
    type_avarie = models.CharField(
        max_length=20,
        choices=TYPE_AVARIE_CHOICES,
        help_text="Nature de l'avarie signalée",
    )
    gravite = models.CharField(
        max_length=10,
        choices=GRAVITE_CHOICES,
        default="MINEURE",
        help_text="Niveau de gravité perçu par le déclarant",
    )
    immobilisation = models.BooleanField(
        default=False,
        help_text="Le véhicule est-il immobilisé suite à cet incident ?",
    )

    class Meta:
        db_table = "gimao_incident_vehicule"
        verbose_name = "Incident véhicule"
        verbose_name_plural = "Incidents véhicule"

    def __str__(self):
        return f"{self.demande_intervention_id} - {self.type_avarie}"


class Sinistre(models.Model):
    """
    Sinistre (accident de la route) rattaché à un ``IncidentVehicule``.

    Relation 1-1 : un ``IncidentVehicule`` ne peut avoir qu'un seul
    ``Sinistre``. La règle métier "un sinistre ne peut être associé qu'à
    un incident de type ``ACCIDENT_ROUTE``" est appliquée par ``clean()``
    (cf. TUS-021) — appeler ``full_clean()`` avant ``save()`` pour la faire
    respecter, ce n'est pas une contrainte de base de données.

    Attributes:
        incident_vehicule: L'incident (accident de la route) concerné.
        date_accident: Date à laquelle l'accident a eu lieu.
        lieu_accident: Lieu de l'accident.
        tiers_impliques: Description des tiers impliqués (personnes,
            véhicules), texte libre.
        degats_constates: Description des dégâts constatés.
        numero_declaration_assurance: Numéro de dossier auprès de l'assurance.
        expertise: Compte-rendu d'expertise, si disponible.
    """

    incident_vehicule = models.OneToOneField(
        IncidentVehicule,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="sinistre",
        help_text="Incident (accident de la route) concerné",
    )
    date_accident = models.DateField(help_text="Date à laquelle l'accident a eu lieu")
    lieu_accident = models.CharField(max_length=255, help_text="Lieu de l'accident")
    tiers_impliques = models.TextField(
        blank=True, null=True, help_text="Description des tiers impliqués"
    )
    degats_constates = models.TextField(
        blank=True, null=True, help_text="Description des dégâts constatés"
    )
    numero_declaration_assurance = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Numéro de dossier auprès de l'assurance",
    )
    expertise = models.TextField(blank=True, null=True, help_text="Compte-rendu d'expertise")

    class Meta:
        db_table = "gimao_sinistre"
        verbose_name = "Sinistre"
        verbose_name_plural = "Sinistres"

    def __str__(self):
        return f"{self.incident_vehicule_id} - {self.lieu_accident} - {self.date_accident}"

    def clean(self):
        super().clean()
        if self.incident_vehicule_id and self.incident_vehicule.type_avarie != "ACCIDENT_ROUTE":
            raise ValidationError(
                "Un sinistre ne peut être associé qu'à un incident de type "
                "« Accident de la route »."
            )
