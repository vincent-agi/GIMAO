from django.core.validators import RegexValidator
from django.db import models
from stock.models import Consommable
from donnees.models import Lieu, Document, Fabricant, Fournisseur
from utilisateur.models import Utilisateur
from gimao.mixins import ArchivableMixin



class ModeleEquipement(models.Model):
    """
    Représente un modèle d'équipement fabriqué par un fabricant.
    """
    nom = models.CharField(max_length=100, help_text="Nom du modèle d'équipement")
    fabricant = models.ForeignKey(Fabricant, on_delete=models.PROTECT, related_name="modeles", help_text="Fabricant du modèle")

    def __str__(self):
        return f"{self.id} - {self.nom} - {self.fabricant.nom}"
    
    class Meta:
        db_table = 'gimao_modele_equipement'
        verbose_name = 'Modèle d\'équipement'
        verbose_name_plural = 'Modèles d\'équipements'
        indexes = [
            models.Index(fields=['nom'], name='modele_nom_idx'),
        ]


class FamilleEquipement(models.Model):
    """
    Représente une famille ou catégorie d'équipements.
    """
    nom = models.CharField(max_length=100, help_text="Nom de la famille d'équipements")
    familleParente = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name="sous_familles", help_text="Famille parente, si applicable")

    def __str__(self):
        return f"{self.id} - {self.nom}"
    
    class Meta:
        db_table = 'gimao_famille_equipement'
        verbose_name = 'Famille d\'équipement'
        verbose_name_plural = 'Familles d\'équipements'
        indexes = [
            models.Index(fields=['nom'], name='famille_nom_idx'),
        ]


class Equipement(ArchivableMixin, models.Model):
    """
    Représente un équipement physique.
    """
    TYPE_CHOICES = [
        ('PEDAGOGIQUE', 'Pédagogique'),
        ('INFRASTRUCTURE', 'Infrastructure'),
        ('MECANIQUE', 'Mécanique'),
        ('ELECTRIQUE', 'Électrique'),
        ('HYDRAULIQUE', 'Hydraulique'),
        ('VEHICULE', 'Véhicule'),
        ('PLURITECHNIQUE', 'Pluritechnique'),
    ]

    numSerie = models.CharField(max_length=100, null=True, blank=True, help_text="Numéro de série de l'équipement")
    reference = models.CharField(max_length=100, null=True, blank=True, help_text="Référence interne ou fournisseur")
    dateCreation = models.DateTimeField(auto_now_add=True, help_text="Date de création de l'équipement")
    designation = models.CharField(max_length=100, help_text="Nom ou désignation de l'équipement")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True, help_text="Type d'équipement")
    dateMiseEnService = models.DateTimeField(null=True, blank=True, help_text="Date de mise en service de l'équipement")
    prixAchat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Prix d'achat de l'équipement")
    lienImage = models.FileField(upload_to='equipement_images/', null=True, blank=True, help_text="Image de l'équipement")
    createurEquipement = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        default=None,
        related_name="equipements_crees",
        help_text="Utilisateur ayant créé l'équipement"
    )
    lieu = models.ForeignKey(Lieu, on_delete=models.PROTECT, related_name="equipements", help_text="Lieu où se trouve l'équipement")
    documents = models.ManyToManyField( Document, 
                                        through='DocumentEquipement', 
                                        blank=True, 
                                        help_text="Documents associés à l'équipement"
                                    )   
    fabricant = models.ForeignKey(Fabricant, on_delete=models.PROTECT, null=True, blank=True, related_name="equipements", help_text="Fabricant de l'équipement")
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, null=True, blank=True, related_name="equipements", help_text="Fournisseur de l'équipement")
    modele = models.ForeignKey(ModeleEquipement, on_delete=models.PROTECT, null=True, blank=True, related_name="equipements", help_text="Modèle de l'équipement")
    famille = models.ForeignKey(FamilleEquipement, null=True, blank=True, on_delete=models.SET_NULL, related_name="equipements", help_text="Famille de l'équipement")
    x = models.FloatField(null=True, blank=True, help_text="Coordonnée X de l'équipement dans le lieu")
    y = models.FloatField(null=True, blank=True, help_text="Coordonnée Y del'équipement dans le lieu")

    def __str__(self):
        return f"{self.id} - {self.designation} - {self.numSerie}"


    def get_dernier_statut(self):
        dernier_statut = self.statuts.order_by('-dateChangement').first()
        return dernier_statut.statut if dernier_statut else "Statut inconnu"
    
    class Meta:
        db_table = 'gimao_equipement'
        verbose_name = 'Équipement'
        verbose_name_plural = 'Équipements'
        indexes = [
            models.Index(fields=['archive', 'designation', 'id'], name='eq_arch_des_id_idx'),
            models.Index(fields=['archive', 'lieu', 'id'], name='eq_arch_lieu_id_idx'),
            models.Index(fields=['archive', 'modele', 'id'], name='eq_arch_mod_id_idx'),
        ]


class StatutEquipement(models.Model):
    """
    Historique des statuts d'un équipement.
    """
    STATUTS_CHOICES = [
        ('EN_FONCTIONNEMENT', 'En fonctionnement'),
        ('DEGRADE', 'Dégradé'),
        ('A_LARRET', 'A l\'arrêt'),
        ('HORS_SERVICE', 'Hors service'),
    ]

    statut = models.CharField(max_length=50, choices=STATUTS_CHOICES, help_text="Statut de l'équipement")
    dateChangement = models.DateTimeField(auto_now_add=True, help_text="Date du changement de statut")
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="statuts", help_text="Équipement concerné")

    def __str__(self):
        return f"{self.id} - {self.statut} - {self.dateChangement}"
    
    class Meta:
        db_table = 'gimao_statut_equipement'
        verbose_name = 'Statut d\'équipement'
        verbose_name_plural = 'Statuts d\'équipements'
        ordering = ['-dateChangement']
        indexes = [
            models.Index(fields=['equipement', '-dateChangement'], name='eq_statut_last_idx'),
        ]


class Compteur(models.Model):
    """
    Représente un compteur ou indicateur lié à un équipement pour la maintenance.
    """
    nomCompteur = models.CharField(max_length=100, null=False, default="Compteur sans nom", help_text="Nom du compteur")
    valeurCourante = models.FloatField(help_text="Valeur actuelle du compteur")
    unite = models.CharField(max_length=50, help_text="Unité de mesure du compteur", default="jours")
    estPrincipal = models.BooleanField(default=False, help_text="Indique si ce compteur est le principal pour l'équipement")
    type = models.CharField(max_length=25, null=False, default="Général", help_text="Type du compteur")
    

    # Relations 
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="compteurs", help_text="Équipement associé au compteur")
    

    def __str__(self):
        return f"{self.id} - {self.nomCompteur} - {self.equipement.designation}"
    
    class Meta:
        db_table = 'gimao_compteur'
        verbose_name = 'Compteur'
        verbose_name_plural = 'Compteurs'


class Declencher(models.Model):
    """
    Association métier entre Compteur et PlanMaintenance
    représentant un seuil de déclenchement.
    """

    derniereIntervention = models.IntegerField(
        default=0,
        help_text="Valeur du compteur à la dernière intervention"
    )
    prochaineMaintenance = models.FloatField(
        help_text="Valeur prévue pour la prochaine maintenance"
    )
    ecartInterventions = models.FloatField(
        help_text="Écart moyen entre interventions"
    )
    estGlissant = models.BooleanField(
        default=False,
        help_text="Indique si le seuil est glissant"
    )
    anticipationJours = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        help_text="Nombre de jours d'anticipation avant l'échéance (calendaire uniquement)"
    )

    compteur = models.ForeignKey(
        Compteur,
        on_delete=models.CASCADE,
        related_name="declenchements"
    )

    planMaintenance = models.ForeignKey(
        'maintenance.PlanMaintenance',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="declenchements"
    )

    def ordinalToISOString(self, ordinal):
        from datetime import date
        try:
            return date.fromordinal(int(ordinal)).isoformat()
        except Exception:
            return "—"

    def __str__(self):
        if self.compteur.type == "Calendaire":
            # Convertir les valeurs ordinales en format date pour l'affichage
            valeurAfficheeProchaine = self.ordinalToISOString(self.prochaineMaintenance)

            return(
                f"{self.id} - {self.compteur.nomCompteur} - Seuil: {valeurAfficheeProchaine} "
                f"(Dernière: {self.ordinalToISOString(self.derniereIntervention)}, Écart: {self.ecartInterventions} {self.compteur.unite},"
                f" Glissant: {'Oui' if self.estGlissant else 'Non'})"
            )

        else:
            valeurAfficheeProchaine = self.prochaineMaintenance
            return (
                f"{self.id} - {self.compteur.nomCompteur} - Seuil: {valeurAfficheeProchaine} {self.compteur.unite }"
                f" (Dernière: {self.derniereIntervention} {self.compteur.unite}, Écart: {self.ecartInterventions} {self.compteur.unite},"
                f" Glissant: {'Oui' if self.estGlissant else 'Non'})"
            )

    class Meta:
        db_table = 'gimao_declencher'
        verbose_name = 'Seuil'
        verbose_name_plural = 'Seuils'
        constraints = [
            models.UniqueConstraint(
                fields=['compteur', 'planMaintenance'],
                name='unique_declenchement_compteur_valeur'
            )
        ]


class Constituer(models.Model):
    """
    Relation many-to-many entre Equipement et Consommable (de l'app stock).
    """
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, help_text="Équipement associé")
    consommable = models.ForeignKey(Consommable, on_delete=models.CASCADE, help_text="Consommable associé")

    def __str__(self):
        return f"{self.id} - Equipement {self.equipement_id} - Consommable {self.consommable_id}"
    
    class Meta:
        db_table = 'gimao_constituer'
        verbose_name = 'Constituer'
        verbose_name_plural = 'Constituer'
        
        
class DocumentEquipement(models.Model):
    """
    Relation many-to-many entre Equipement et Document (de l'app donnees).
    """
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, help_text="Équipement associé")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, help_text="Document associé")

    def __str__(self):
        return f"{self.id} - Equipement {self.equipement_id} - Document {self.document_id}"
    
    class Meta:
        db_table = 'gimao_document_equipement'
        verbose_name = 'Lien Document-Equipement'
        verbose_name_plural = 'Liens Documents-Equipements'


VIN_VALIDATOR = RegexValidator(
    regex=r'^[A-HJ-NPR-Z0-9]{17}$',
    message="Le VIN doit comporter exactement 17 caractères alphanumériques (hors I, O, Q, exclus par la norme ISO 3779).",
)

IMMATRICULATION_SIV_VALIDATOR = RegexValidator(
    regex=r'^[A-Z]{2}-\d{3}-[A-Z]{2}$',
    message="L'immatriculation doit respecter le format SIV français : AA-123-AA.",
)


class VehiculeProfile(models.Model):
    """
    Profil véhicule d'un équipement, en relation un-à-un avec ``Equipement``.

    Porte les champs spécifiques à un véhicule automobile/poids lourd (VIN,
    immatriculation, genre, énergie, caractéristiques réglementaires) sans
    polluer le modèle générique ``Equipement``, qui reste le socle commun à
    tous les types d'équipements (cf. ADR-001, ``docs/adr/0001-modelisation-vehicule.md``).

    Un ``Equipement`` n'a un ``VehiculeProfile`` que si son ``type`` vaut
    ``'VEHICULE'`` ; la création des deux est faite conjointement par
    ``equipement.services.create_vehicule`` dans une transaction atomique.

    Attributes:
        equipement: L'``Equipement`` générique dont ce profil complète les
            données. Clé primaire du profil (relation 1-1 stricte).
        vin: Numéro d'identification du véhicule (17 caractères, unique),
            conforme à la norme ISO 3779.
        immatriculation: Plaque d'immatriculation au format SIV français
            (``AA-123-AA``), unique.
        genre: Catégorie du véhicule, utilisée notamment pour déterminer la
            catégorie de permis de conduire requise pour l'affectation d'un
            conducteur (cf. Milestone M4).
        energie: Type d'énergie/motorisation du véhicule.
        co2: Émissions de CO2 en grammes par kilomètre (le cas échéant).
        puissanceFiscale: Puissance fiscale du véhicule, en chevaux fiscaux.
        ptac: Poids total autorisé en charge, en kilogrammes.
    """

    GENRE_CHOICES = [
        ('VL', 'Véhicule léger'),
        ('PL', 'Poids lourd'),
        ('UTILITAIRE', 'Utilitaire'),
        ('REMORQUE', 'Remorque'),
    ]

    ENERGIE_CHOICES = [
        ('ESSENCE', 'Essence'),
        ('DIESEL', 'Diesel'),
        ('ELECTRIQUE', 'Électrique'),
        ('HYBRIDE', 'Hybride'),
        ('GPL', 'GPL'),
        ('AUTRE', 'Autre'),
    ]

    equipement = models.OneToOneField(
        Equipement,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name='vehicule_profile',
        help_text="Équipement générique dont ce profil complète les données véhicule",
    )
    vin = models.CharField(
        max_length=17,
        unique=True,
        validators=[VIN_VALIDATOR],
        help_text="Numéro d'identification du véhicule (VIN), 17 caractères ISO 3779",
    )
    immatriculation = models.CharField(
        max_length=9,
        unique=True,
        validators=[IMMATRICULATION_SIV_VALIDATOR],
        help_text="Plaque d'immatriculation au format SIV français (AA-123-AA)",
    )
    genre = models.CharField(
        max_length=20,
        choices=GENRE_CHOICES,
        help_text="Catégorie du véhicule (VL, PL, utilitaire, remorque)",
    )
    energie = models.CharField(
        max_length=20,
        choices=ENERGIE_CHOICES,
        help_text="Type d'énergie/motorisation du véhicule",
    )
    co2 = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Émissions de CO2 en grammes par kilomètre",
    )
    puissanceFiscale = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Puissance fiscale en chevaux fiscaux",
    )
    ptac = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Poids total autorisé en charge, en kilogrammes",
    )

    def __str__(self):
        return f"{self.equipement_id} - {self.immatriculation} - {self.vin}"

    class Meta:
        db_table = 'gimao_vehicule_profile'
        verbose_name = 'Profil véhicule'
        verbose_name_plural = 'Profils véhicule'
        indexes = [
            models.Index(fields=['immatriculation'], name='vehicule_immat_idx'),
            models.Index(fields=['vin'], name='vehicule_vin_idx'),
        ]
