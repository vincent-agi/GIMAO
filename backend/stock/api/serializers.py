from rest_framework import serializers

from stock.models import Consommable, EstCompatible, Magasin, PorterSur, Stocker


class MagasinSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Magasin"""

    class Meta:
        model = Magasin
        fields = "__all__"


class MagasinDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour le modèle Magasin avec informations de l'adresse"""

    adresse_details = serializers.SerializerMethodField()

    class Meta:
        model = Magasin
        fields = ["id", "nom", "estMobile", "adresse", "adresse_details", "archive"]

    def get_adresse_details(self, obj):
        if obj.adresse:
            return {
                "id": obj.adresse.id,
                "rue": getattr(obj.adresse, "rue", None),
                "codePostal": getattr(obj.adresse, "codePostal", None),
                "ville": getattr(obj.adresse, "ville", None),
            }
        return None


class ConsommableSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Consommable"""

    class Meta:
        model = Consommable
        fields = "__all__"


class FournitureConsommableSerializer(serializers.ModelSerializer):
    """Serializer pour les fournitures (PorterSur) avec détails du fournisseur et fabricant"""

    fournisseur_nom = serializers.CharField(source="fournisseur.nom", read_only=True)
    fabricant_nom = serializers.CharField(source="fabricant.nom", read_only=True)

    class Meta:
        model = PorterSur
        fields = [
            "id",
            "fournisseur",
            "fournisseur_nom",
            "fabricant",
            "fabricant_nom",
            "quantite",
            "prix_unitaire",
            "date_reference_prix",
        ]


class StockerSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Stocker (stock en magasin)"""

    magasin_nom = serializers.CharField(source="magasin.nom", read_only=True)

    class Meta:
        model = Stocker
        fields = ["id", "magasin", "magasin_nom", "quantite"]


class ConsommableDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour le modèle Consommable avec informations du magasin"""

    fournitures = FournitureConsommableSerializer(many=True, read_only=True)
    stocks = StockerSerializer(many=True, read_only=True)
    quantite_totale = serializers.SerializerMethodField()

    class Meta:
        model = Consommable
        fields = [
            "id",
            "designation",
            "lienImageConsommable",
            "magasins",
            "fournitures",
            "stocks",
            "quantite_totale",
            "seuilStockFaible",
            "documents",
            "archive",
        ]

    def get_quantite_totale(self, obj):
        # Somme des quantités de tous les stocks
        total = sum(stock.quantite for stock in obj.stocks.all())
        return total


class PorterSurSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle PorterSur (fourniture de consommable)"""

    distribution = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="Liste de {magasin: id, quantite: int} pour la distribution",
    )

    class Meta:
        model = PorterSur
        fields = "__all__"


class EstCompatibleSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle EstCompatible"""

    class Meta:
        model = EstCompatible
        fields = "__all__"
