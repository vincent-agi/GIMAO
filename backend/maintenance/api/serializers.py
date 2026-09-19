from rest_framework import serializers

from donnees.api.serializers import DocumentSerializer
from donnees.models import Document
from equipement.models import Compteur, Equipement
from maintenance.models import (
    BonTravail,
    BonTravailConsommable,
    DemandeIntervention,
    PlanMaintenance,
    PlanMaintenanceConsommable,
    TypePlanMaintenance,
)
from stock.models import Consommable
from utilisateur.models import Utilisateur

# ==================== SERIALIZERS SIMPLES ====================


class UtilisateurSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour Utilisateur"""

    class Meta:
        model = Utilisateur
        fields = ["id", "nomUtilisateur", "email", "prenom", "nomFamille"]
        ref_name = "MaintenanceUtilisateurSimple"


class EquipementSimpleSerializer(serializers.ModelSerializer):
    lieu = serializers.CharField(source="lieu.nomLieu")
    dernier_statut = serializers.SerializerMethodField()

    class Meta:
        model = Equipement
        fields = ["id", "reference", "designation", "lieu", "dernier_statut"]
        ref_name = "EquipementSimpleSerializer"

    def get_dernier_statut(self, obj):
        statuts = getattr(obj, "prefetched_statuts", None)
        if statuts is None:
            statut = obj.statuts.order_by("-dateChangement").first()
        else:
            statut = statuts[0] if statuts else None

        if statut:
            date_changement = statut.dateChangement
            if hasattr(date_changement, "isoformat"):
                date_changement = date_changement.isoformat()
            return {"id": statut.id, "statut": statut.statut, "dateChangement": date_changement}
        return None


class ConsommableSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour Consommable"""

    class Meta:
        model = Consommable
        fields = ["id", "designation"]
        ref_name = "MaintenanceConsommableSimple"


class DocumentSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour Document"""

    class Meta:
        model = Document
        fields = ["id", "nomDocument", "cheminAcces"]
        ref_name = "MaintenanceDocumentSimple"


class CompteurSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour Compteur"""

    class Meta:
        model = Compteur
        fields = ["id", "nomCompteur", "valeurCourante"]
        ref_name = "MaintenanceCompteurSimple"


# ==================== DEMANDE INTERVENTION ====================


class DemandeInterventionSerializer(serializers.ModelSerializer):
    """Serializer pour DemandeIntervention"""

    utilisateur = UtilisateurSimpleSerializer(read_only=True)
    equipement = EquipementSimpleSerializer(read_only=True)

    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(), source="utilisateur", write_only=True
    )
    equipement_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipement.objects.all(), source="equipement", write_only=True
    )

    statut_suppose = serializers.ChoiceField(
        choices=DemandeIntervention.STATUTS_EQUIPEMENT_CHOICES, required=True
    )

    class Meta:
        model = DemandeIntervention
        fields = [
            "id",
            "nom",
            "commentaire",
            "statut",
            "statut_suppose",
            "date_creation",
            "date_changementStatut",
            "equipement",
            "utilisateur",
            "utilisateur_id",
            "equipement_id",
            "archive",
        ]
        read_only_fields = ["id", "date_creation", "date_changementStatut", "statut"]

    def create(self, validated_data):
        from django.utils import timezone

        validated_data["date_creation"] = timezone.now()
        validated_data["date_changementStatut"] = timezone.now()
        validated_data["statut"] = "EN_ATTENTE"

        return super().create(validated_data)


class DemandeInterventionDetailSerializer(DemandeInterventionSerializer):
    """Serializer détaillé avec les documents et le bon de travail"""

    documentsDI = DocumentSerializer(source="documents", many=True, read_only=True)

    class Meta(DemandeInterventionSerializer.Meta):
        fields = DemandeInterventionSerializer.Meta.fields + ["documentsDI"]


# ==================== BON TRAVAIL ====================


class BonTravailConsommableWriteSerializer(serializers.Serializer):
    consommable_id = serializers.PrimaryKeyRelatedField(
        queryset=Consommable.objects.all(), source="consommable"
    )
    quantite_utilisee = serializers.IntegerField(min_value=0, required=False, default=0)


class BonTravailSerializer(serializers.ModelSerializer):
    """Serializer pour BonTravail"""

    demande_intervention = serializers.PrimaryKeyRelatedField(
        queryset=DemandeIntervention.objects.all()
    )
    equipement_designation = serializers.CharField(
        source="demande_intervention.equipement.designation", read_only=True
    )
    responsable = UtilisateurSimpleSerializer(read_only=True)
    utilisateur_assigne = UtilisateurSimpleSerializer(many=True, read_only=True)

    responsable_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source="responsable",
        write_only=True,
        required=False,
        allow_null=True,
    )
    utilisateur_assigne_ids = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source="utilisateur_assigne",
        write_only=True,
        many=True,
        required=False,
    )

    consommables_ids = serializers.PrimaryKeyRelatedField(
        queryset=Consommable.objects.all(), write_only=True, many=True, required=False
    )
    consommables = BonTravailConsommableWriteSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = BonTravail
        fields = [
            "id",
            "nom",
            "diagnostic",
            "type",
            "date_assignation",
            "date_cloture",
            "date_debut",
            "date_fin",
            "date_prevue",
            "duree_previsionnelle",
            "statut",
            "commentaire",
            "commentaire_refus_cloture",
            "demande_intervention",
            "equipement_designation",
            "responsable",
            "utilisateur_assigne",
            "responsable_id",
            "utilisateur_assigne_ids",
            "consommables_ids",
            "consommables",
            "archive",
        ]

    def _sync_consommables(self, bon_travail, consommables_dict):
        if consommables_dict is None:
            return

        ids = set(consommables_dict.keys())

        BonTravailConsommable.objects.filter(bon_travail=bon_travail).exclude(
            consommable_id__in=ids
        ).delete()

        existing = {
            assoc.consommable_id: assoc
            for assoc in BonTravailConsommable.objects.filter(
                bon_travail=bon_travail, consommable_id__in=ids
            )
        }

        to_create = []
        to_update = []
        for consommable_id, quantite in consommables_dict.items():
            assoc = existing.get(consommable_id)
            if assoc is None:
                to_create.append(
                    BonTravailConsommable(
                        bon_travail=bon_travail,
                        consommable_id=consommable_id,
                        quantite_utilisee=quantite,
                    )
                )
            elif assoc.quantite_utilisee != quantite:
                assoc.quantite_utilisee = quantite
                to_update.append(assoc)

        if to_create:
            BonTravailConsommable.objects.bulk_create(to_create)
        if to_update:
            BonTravailConsommable.objects.bulk_update(to_update, ["quantite_utilisee"])

    def _extract_consommables_dict(self, validated_data):
        """Retourne dict[int consommable_id] -> int quantite_utilisee, ou None si non fourni."""
        items = validated_data.pop("consommables", None)
        ids_only = validated_data.pop("consommables_ids", None)

        if items is not None:
            result = {}
            for item in items:
                consommable = item.get("consommable")
                quantite = int(item.get("quantite_utilisee", 0) or 0)
                result[int(consommable.id)] = max(0, quantite)
            return result

        if ids_only is not None:
            return {int(consommable.id): 0 for consommable in ids_only}

        return None

    def create(self, validated_data):
        consommables_dict = self._extract_consommables_dict(validated_data)
        bon = super().create(validated_data)
        self._sync_consommables(bon, consommables_dict)
        return bon

    def update(self, instance, validated_data):
        consommables_dict = self._extract_consommables_dict(validated_data)
        bon = super().update(instance, validated_data)
        self._sync_consommables(bon, consommables_dict)
        return bon


class BonTravailListStockSerializer(serializers.ModelSerializer):
    """Serializer pour la liste de BonTravail avec les consommables"""

    demande_intervention = DemandeInterventionDetailSerializer(read_only=True)
    responsable = UtilisateurSimpleSerializer(read_only=True)
    utilisateur_assigne = UtilisateurSimpleSerializer(many=True, read_only=True)
    documentsBT = DocumentSerializer(source="documents", many=True, read_only=True)
    documentsDI = DocumentSerializer(
        source="demande_intervention.documents", many=True, read_only=True
    )
    consommables = serializers.SerializerMethodField()

    class Meta:
        model = BonTravail
        fields = [
            "id",
            "nom",
            "diagnostic",
            "type",
            "date_assignation",
            "date_cloture",
            "date_debut",
            "date_fin",
            "date_prevue",
            "statut",
            "commentaire",
            "commentaire_refus_cloture",
            "pieces_recuperees",
            "date_recuperation",
            "documentsBT",
            "documentsDI",
            "consommables",
            "demande_intervention",
            "responsable",
            "utilisateur_assigne",
        ]

    def get_consommables(self, obj):
        """Retourne les consommables avec leur statut de distribution"""
        associations = list(getattr(obj, "prefetched_consommables", []))
        if not associations:
            associations = (
                BonTravailConsommable.objects.filter(bon_travail=obj)
                .select_related("consommable")
                .prefetch_related("reservations__magasin")
            )
        consommables = []
        for assoc in associations:
            stocks = list(assoc.consommable.stocks.all())
            reservations = list(assoc.reservations.all())

            consommables.append(
                {
                    "consommable": assoc.consommable.id,
                    "designation": assoc.consommable.designation,
                    "image": assoc.consommable.lienImageConsommable.name.lstrip("/")
                    if assoc.consommable.lienImageConsommable
                    else None,
                    "quantite": assoc.quantite_utilisee,
                    "distribue": assoc.estConfirme,
                    "date_distribution": assoc.date_confirme.isoformat()
                    if assoc.date_confirme
                    else None,
                    "magasin_reserve": assoc.magasin_reserve_id,
                    "stock_total": sum(stock.quantite for stock in stocks),
                    "stocks": [
                        {
                            "magasin": stock.magasin_id,
                            "magasin_nom": stock.magasin.nom,
                            "quantite": stock.quantite,
                        }
                        for stock in stocks
                    ],
                    "magasins_reserves": [
                        {
                            "magasin_id": reservation.magasin_id,
                            "magasin_nom": reservation.magasin.nom,
                            "quantite": reservation.quantite,
                        }
                        for reservation in reservations
                    ],
                }
            )

        return consommables


class BonTravailDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour BonTravail"""

    demande_intervention = DemandeInterventionDetailSerializer(read_only=True)
    responsable = UtilisateurSimpleSerializer(read_only=True)
    utilisateur_assigne = UtilisateurSimpleSerializer(many=True, read_only=True)
    documentsBT = DocumentSerializer(source="documents", many=True, read_only=True)
    documentsDI = DocumentSerializer(
        source="demande_intervention.documents", many=True, read_only=True
    )
    consommables = serializers.SerializerMethodField()

    class Meta:
        model = BonTravail
        fields = [
            "id",
            "nom",
            "diagnostic",
            "type",
            "date_assignation",
            "date_cloture",
            "date_debut",
            "date_fin",
            "date_prevue",
            "duree_previsionnelle",
            "statut",
            "commentaire",
            "commentaire_refus_cloture",
            "documentsBT",
            "documentsDI",
            "consommables",
            "demande_intervention",
            "responsable",
            "utilisateur_assigne",
            "archive",
        ]

    def get_consommables(self, obj):
        associations = list(getattr(obj, "prefetched_consommables", []))
        if not associations:
            associations = BonTravailConsommable.objects.filter(bon_travail=obj).select_related(
                "consommable"
            )
        return [
            {
                "consommable": assoc.consommable.id,
                "designation": assoc.consommable.designation,
                "image": assoc.consommable.lienImageConsommable.name.lstrip("/")
                if assoc.consommable.lienImageConsommable
                else None,
                "quantite": assoc.quantite_utilisee,
            }
            for assoc in associations
        ]


# ==================== TYPE PLAN MAINTENANCE ====================


class TypePlanMaintenanceSerializer(serializers.ModelSerializer):
    """Serializer pour TypePlanMaintenance"""

    class Meta:
        model = TypePlanMaintenance
        fields = ["id", "libelle"]


# ==================== PLAN MAINTENANCE ====================


class PlanMaintenanceConsommableSerializer(serializers.ModelSerializer):
    """Serializer pour la table d'association"""

    consommable = ConsommableSimpleSerializer(read_only=True)
    consommable_id = serializers.PrimaryKeyRelatedField(
        queryset=Consommable.objects.all(), source="consommable", write_only=True
    )

    class Meta:
        model = PlanMaintenanceConsommable
        fields = ["consommable", "consommable_id", "quantite_necessaire"]


class PlanMaintenanceSerializer(serializers.ModelSerializer):
    """Serializer pour PlanMaintenance"""

    documents = DocumentSerializer(many=True, read_only=True)
    consommables = serializers.SerializerMethodField()
    compteur_id = serializers.SerializerMethodField()

    type_id = serializers.IntegerField(source="type_plan_maintenance.id", read_only=True)

    class Meta:
        model = PlanMaintenance
        fields = ["id", "nom", "type_id", "compteur_id", "documents", "consommables"]

    def get_compteur_id(self, obj):
        decl = obj.declenchements.first()
        return decl.compteur_id if decl else None

    def get_consommables(self, obj):
        associations = PlanMaintenanceConsommable.objects.filter(
            plan_maintenance=obj
        ).select_related("consommable")
        return [
            {"consommable": assoc.consommable.id, "quantite": assoc.quantite_necessaire}
            for assoc in associations
        ]


class PlanMaintenanceDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé avec consommables et documents"""

    type = serializers.IntegerField(source="type_plan_maintenance.id", read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    consommables = serializers.SerializerMethodField()

    class Meta:
        model = PlanMaintenance
        fields = ["id", "nom", "type", "documents", "consommables"]

    def get_consommables(self, obj):
        associations = PlanMaintenanceConsommable.objects.filter(
            plan_maintenance=obj
        ).select_related("consommable")
        return [
            {"consommable": assoc.consommable.id, "quantite": assoc.quantite_necessaire}
            for assoc in associations
        ]
