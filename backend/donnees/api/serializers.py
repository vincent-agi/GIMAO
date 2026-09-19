from rest_framework import serializers

from donnees.models import Adresse, Document, Fabricant, Fournisseur, Lieu, TypeDocument


class AdresseSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Adresse — tous les champs sont optionnels"""

    class Meta:
        model = Adresse
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # L'adresse est facultative : aucun champ n'est obligatoire
        for field_name, field in self.fields.items():
            if field_name == "id":
                continue
            field.required = False
            if hasattr(field, "allow_blank"):
                field.allow_blank = True
            if hasattr(field, "allow_null"):
                field.allow_null = True


class LieuSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Lieu"""

    lieuParent = serializers.PrimaryKeyRelatedField(
        queryset=Lieu.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Lieu
        fields = "__all__"


class LieuDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour le modèle Lieu avec les relations"""

    lieuParent = serializers.SerializerMethodField()
    sous_lieux = serializers.SerializerMethodField()
    hierarchie_complete = serializers.SerializerMethodField()

    class Meta:
        model = Lieu
        fields = [
            "id",
            "nomLieu",
            "typeLieu",
            "lienPlan",
            "lieuParent",
            "x",
            "y",
            "sous_lieux",
            "hierarchie_complete",
        ]

    def get_lieuParent(self, obj):
        if obj.lieuParent:
            return {
                "id": obj.lieuParent.id,
                "nomLieu": obj.lieuParent.nomLieu,
                "typeLieu": obj.lieuParent.typeLieu,
            }
        return None

    def get_sous_lieux(self, obj):
        sous_lieux = Lieu.objects.filter(lieuParent=obj)
        return [
            {"id": lieu.id, "nomLieu": lieu.nomLieu, "typeLieu": lieu.typeLieu}
            for lieu in sous_lieux
        ]

    def get_hierarchie_complete(self, obj):
        """Méthode récursive pour obtenir la hiérarchie complète des lieux parents"""
        hierarchy = []
        current_lieu = obj.lieuParent
        while current_lieu:
            hierarchy.append(
                {
                    "id": current_lieu.id,
                    "nomLieu": current_lieu.nomLieu,
                    "typeLieu": current_lieu.typeLieu,
                }
            )
            current_lieu = current_lieu.lieuParent
        return hierarchy[::-1]  # Inverser pour avoir du plus ancien au plus récent


class TypeDocumentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle TypeDocument"""

    class Meta:
        model = TypeDocument
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Document.

    Format historique (utilisé par le front):
    - titre, type, type_nom, path

    On supporte aussi la création via multipart avec:
    - cheminAcces (fichier)
    - typeDocument_id (alias) ou typeDocument
    - nomDocument (optionnel)
    """

    # Champs d'écriture (création via CRUD)
    typeDocument = serializers.PrimaryKeyRelatedField(
        queryset=TypeDocument.objects.all(),
        write_only=True,
        required=False,
    )
    typeDocument_id = serializers.IntegerField(write_only=True, required=False)
    cheminAcces = serializers.FileField(write_only=True, required=True)
    nomDocument = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Champs de lecture (compat)
    titre = serializers.CharField(source="nomDocument", read_only=True)
    type = serializers.IntegerField(source="typeDocument.id", read_only=True)
    type_nom = serializers.CharField(source="typeDocument.nomTypeDocument", read_only=True)
    path = serializers.CharField(source="cheminAcces.name", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "titre",
            "type",
            "type_nom",
            "path",
            "nomDocument",
            "cheminAcces",
            "typeDocument",
            "typeDocument_id",
        ]

    def validate(self, attrs):
        # Normalise l'alias typeDocument_id -> typeDocument.
        if attrs.get("typeDocument") is None and attrs.get("typeDocument_id") is not None:
            try:
                attrs["typeDocument"] = TypeDocument.objects.get(id=int(attrs["typeDocument_id"]))
            except Exception:
                raise serializers.ValidationError(
                    {"typeDocument_id": "TypeDocument invalide."}
                ) from None

        if attrs.get("typeDocument") is None:
            raise serializers.ValidationError(
                {"typeDocument": "Le champ typeDocument (ou typeDocument_id) est requis."}
            )

        return attrs

    def create(self, validated_data):
        # Si aucun nom fourni, on prend le nom du fichier.
        nom = (validated_data.get("nomDocument") or "").strip()
        if not nom:
            uploaded = validated_data.get("cheminAcces")
            if uploaded is not None and getattr(uploaded, "name", None):
                validated_data["nomDocument"] = uploaded.name
        return super().create(validated_data)


class DocumentSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour le modèle Document (sans nested objects)"""

    class Meta:
        model = Document
        fields = ["id", "nomDocument", "cheminAcces", "typeDocument"]
        ref_name = "DonneesDocumentSimple"


class FabricantSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Fabricant"""

    adresse = AdresseSerializer(read_only=True)

    class Meta:
        model = Fabricant
        fields = ["id", "nom", "email", "numTelephone", "serviceApresVente", "adresse"]


class FabricantSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour le modèle Fabricant (sans nested objects)"""

    class Meta:
        model = Fabricant
        fields = ["id", "nom"]
        ref_name = "DonneesFabricantSimple"


class FournisseurSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Fournisseur"""

    adresse = AdresseSerializer(read_only=True)

    class Meta:
        model = Fournisseur
        fields = ["id", "nom", "email", "numTelephone", "serviceApresVente", "adresse"]


class FournisseurSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour le modèle Fournisseur (sans nested objects)"""

    class Meta:
        model = Fournisseur
        fields = ["id", "nom"]
        ref_name = "DonneesFournisseurSimple"
