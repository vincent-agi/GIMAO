from django.db import models


class Lieu(models.Model):
    """
    Représente un emplacement physique dans la hiérarchie des lieux (site, bâtiment, salle…).

    Les lieux sont organisés en arbre via la clé étrangère ``lieuParent``. Un lieu sans parent
    est une racine (ex : site principal). Les coordonnées x/y permettent de positionner un lieu
    sur le plan de son parent.
    """

    nomLieu = models.CharField(max_length=50, help_text="Nom du lieu.")
    typeLieu = models.CharField(
        max_length=50,
        help_text="Informations complémentaires optionnelles sur le type de lieu renseigné.",
    )
    lienPlan = models.CharField(
        max_length=200, blank=True, null=True, help_text="Lien vers un plan du lieu."
    )
    lieuParent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="Pointeur désignant la structure (un autre lieu) où se trouve l'élément en question.",
    )
    x = models.FloatField(
        null=True, blank=True, help_text="Coordonnée X du lieu par rapport à son lieu parent."
    )
    y = models.FloatField(
        null=True, blank=True, help_text="Coordonnée Y du lieu par rapport à son lieu parent."
    )

    class Meta:
        db_table = "gimao_lieu"
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"
        indexes = [
            models.Index(fields=["nomLieu"], name="lieu_nom_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.nomLieu}"


class TypeDocument(models.Model):
    """
    Catégorie de document (ex : notice technique, bon de commande, certificat).
    Utilisée pour classer les documents attachés aux équipements, DI et BT.
    """

    nomTypeDocument = models.CharField(max_length=50)

    class Meta:
        db_table = "gimao_type_document"
        verbose_name = "Type de document"
        verbose_name_plural = "Types de document"
        indexes = [
            models.Index(fields=["nomTypeDocument"], name="typedoc_nom_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.nomTypeDocument}"


class Document(models.Model):
    """
    Fichier attaché à une entité du système (équipement, DI, BT, plan de maintenance).

    Le fichier est stocké dans le dossier ``media/documents/``. Un même document peut être
    associé à plusieurs entités via les tables d'association dédiées (``DocumentEquipement``,
    ``BonTravailDocument``, etc.).
    """

    nomDocument = models.CharField(max_length=100, help_text="Nom du document.")
    cheminAcces = models.FileField(
        upload_to="documents/", help_text="Chemin d'accès au fichier du document."
    )
    typeDocument = models.ForeignKey(
        TypeDocument, on_delete=models.CASCADE, help_text="Type du document."
    )

    class Meta:
        db_table = "gimao_document"
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"{self.id} - {self.nomDocument}"


class Fabricant(models.Model):
    """
    Représente un fabricant d'équipements.
    """

    nom = models.CharField(max_length=100, help_text="Nom du fabricant")
    email = models.EmailField(
        max_length=191, blank=True, null=True, help_text="Adresse email du fabricant"
    )
    numTelephone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Numéro de téléphone du fabricant"
    )
    serviceApresVente = models.BooleanField(
        default=False, help_text="Indique si le fabricant propose un service après-vente"
    )
    adresse = models.ForeignKey(
        "Adresse", on_delete=models.CASCADE, null=True, blank=True, help_text="Adresse du fabricant"
    )

    class Meta:
        db_table = "gimao_fabricant"
        verbose_name = "Fabricant"
        verbose_name_plural = "Fabricants"
        indexes = [
            models.Index(fields=["nom"], name="fabricant_nom_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.nom}"


class Fournisseur(models.Model):
    """
    Représente un fournisseur d'équipements.
    """

    nom = models.CharField(max_length=100, help_text="Nom du fournisseur")
    email = models.EmailField(
        max_length=191, blank=True, null=True, help_text="Adresse email du fournisseur"
    )
    numTelephone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Numéro de téléphone du fournisseur"
    )
    serviceApresVente = models.BooleanField(
        default=False, help_text="Indique si le fournisseur propose un service après-vente"
    )
    adresse = models.ForeignKey(
        "Adresse",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Adresse du fournisseur",
    )

    class Meta:
        db_table = "gimao_fournisseur"
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        indexes = [
            models.Index(fields=["nom"], name="fournisseur_nom_idx"),
        ]

    def __str__(self):
        return f"{self.id} - {self.nom}"


class Adresse(models.Model):
    """
    Représente une adresse physique.
    """

    numero = models.CharField(max_length=10, help_text="Numéro de l'adresse")
    rue = models.CharField(max_length=255, help_text="Nom de la rue")
    ville = models.CharField(max_length=100, help_text="Nom de la ville")
    code_postal = models.CharField(max_length=20, help_text="Code postal")
    pays = models.CharField(max_length=100, help_text="Nom du pays")
    complement = models.CharField(
        max_length=255, blank=True, null=True, help_text="Complément d'adresse optionnel"
    )

    class Meta:
        db_table = "gimao_adresse"
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"

    def __str__(self):
        parts = [str(self.id)]

        # Adresse (numéro + rue)
        rue_complete = f"{self.numero} {self.rue}".strip()
        if rue_complete:
            parts.append(rue_complete)

        # Localisation
        loc_parts = [p for p in [self.ville, self.code_postal, self.pays] if p]
        if loc_parts:
            parts.append(", ".join(loc_parts))

        return " - ".join(parts)
