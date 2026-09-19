from django.core.validators import MinValueValidator
from django.db import models

from donnees.models import Adresse
from gimao.mixins import ArchivableMixin


class Magasin(ArchivableMixin, models.Model):
    """
    Lieu de stockage des consommables.

    Un magasin peut être fixe (atelier, réserve) ou mobile (camion de technicien).
    Le champ ``estMobile`` distingue ces deux cas. Le stock par consommable est suivi
    via le modèle intermédiaire ``Stocker``.
    """

    nom = models.CharField(max_length=100)
    estMobile = models.BooleanField(default=False)
    adresse = models.ForeignKey(
        Adresse, on_delete=models.CASCADE, null=True, blank=True, help_text="Adresse du magasin"
    )

    class Meta:
        db_table = "gimao_magasin"
        verbose_name = "Magasin"
        verbose_name_plural = "Magasins"

    def __str__(self):
        return f"{self.id} - {self.nom}"


class Consommable(ArchivableMixin, models.Model):
    """
    Pièce ou fourniture utilisable dans le cadre d'une intervention de maintenance.

    Le stock d'un consommable est réparti entre plusieurs magasins via ``Stocker``.
    ``seuilStockFaible`` déclenche une alerte visuelle lorsque le stock global passe
    en dessous de cette valeur. Les achats sont enregistrés via ``PorterSur``.
    """

    designation = models.CharField(max_length=50)
    lienImageConsommable = models.ImageField(upload_to="images/", null=True, blank=True)
    magasins = models.ManyToManyField(
        Magasin, through="Stocker", related_name="consommables", blank=True
    )
    seuilStockFaible = models.IntegerField(
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
        help_text="Seuil en dessous duquel le stock est considéré comme faible",
    )
    documents = models.ManyToManyField(
        "donnees.Document", blank=True, help_text="Documents associés au consommable"
    )

    class Meta:
        db_table = "gimao_consommable"
        verbose_name = "Consommable"
        verbose_name_plural = "Consommables"
        indexes = [
            models.Index(fields=["archive", "designation", "id"], name="cons_arch_des_idx"),
            models.Index(fields=["archive", "seuilStockFaible", "id"], name="cons_arch_seuil_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.designation}"


class PorterSur(models.Model):
    """
    Enregistrement d'un achat de consommable (fourniture).

    Lie un consommable à un fournisseur et un fabricant pour un achat donné.
    La contrainte ``unique_together`` empêche d'enregistrer deux achats identiques
    (même consommable, fournisseur, fabricant et date). La distribution du stock
    par magasin est gérée côté viewset lors de la création.
    """

    # Relations
    consommable = models.ForeignKey(
        Consommable, on_delete=models.CASCADE, related_name="fournitures"
    )
    fournisseur = models.ForeignKey(
        "donnees.Fournisseur", on_delete=models.CASCADE, related_name="fournitures"
    )
    fabricant = models.ForeignKey(
        "donnees.Fabricant", on_delete=models.CASCADE, related_name="fournitures"
    )

    # Attributs
    quantite = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    prix_unitaire = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    date_reference_prix = models.DateTimeField()

    class Meta:
        db_table = "gimao_porter_sur"
        verbose_name = "Fourniture de consommable"
        verbose_name_plural = "Fournitures de consommables"
        unique_together = ["consommable", "fournisseur", "fabricant", "date_reference_prix"]

    def __str__(self):
        return f"{self.id} - {self.consommable.designation} - {self.fournisseur.nom} - {self.fabricant.nom} ({self.date_reference_prix})"


class Stocker(models.Model):
    """
    Niveau de stock d'un consommable dans un magasin donné.

    Table intermédiaire de la relation many-to-many entre ``Consommable`` et ``Magasin``.
    La quantité est mise à jour à chaque confirmation de consommable sur un BT (décrémentation)
    ou à chaque enregistrement d'achat via ``PorterSur`` (incrémentation).
    """

    consommable = models.ForeignKey(Consommable, on_delete=models.CASCADE, related_name="stocks")
    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE, related_name="stocks")
    quantite = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        db_table = "gimao_stocker"
        verbose_name = "Stock en magasin"
        verbose_name_plural = "Stocks en magasin"
        unique_together = ["consommable", "magasin"]
        indexes = [
            models.Index(fields=["magasin", "consommable"], name="stock_mag_cons_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.consommable.designation} - {self.magasin.nom} : {self.quantite}"


class EstCompatible(models.Model):
    """
    Déclare la compatibilité entre un consommable et un modèle d'équipement.

    Permet de filtrer les consommables utilisables lors de la création d'un BT,
    en ne proposant que ceux compatibles avec le modèle de l'équipement concerné.
    """

    consommable = models.ForeignKey(Consommable, on_delete=models.CASCADE)
    modeleEquipement = models.ForeignKey("equipement.ModeleEquipement", on_delete=models.CASCADE)

    class Meta:
        db_table = "gimao_estcompatible"
        verbose_name = "Compatibilité consommable-modèle"
        verbose_name_plural = "Compatibilités consommable-modèle"
        unique_together = ["consommable", "modeleEquipement"]

    def __str__(self):
        return f"{self.id} - {self.consommable.designation} - {self.modeleEquipement.nom}"
