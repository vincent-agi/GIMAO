from django.db.models import Prefetch
from rest_framework import serializers

from donnees.api.serializers import (
    FabricantSimpleSerializer,
    FournisseurSimpleSerializer,
    LieuSerializer,
)
from donnees.models import Fabricant
from equipement.models import (
    Compteur,
    Constituer,
    Declencher,
    Equipement,
    FamilleEquipement,
    ModeleEquipement,
    StatutEquipement,
    VehiculeProfile,
)
from maintenance.models import BonTravail, PlanMaintenance


class EquipementSerializer(serializers.ModelSerializer):
    # Fetcg le dernier statut de l'équipement
    statut = serializers.SerializerMethodField()
    modele = serializers.CharField(source="modele.nom", read_only=True)
    lieu = LieuSerializer(read_only=True)

    def get_statut(self, obj):
        prefetched_statuts = getattr(obj, "prefetched_statuts", None)
        if prefetched_statuts is not None:
            statut = prefetched_statuts[0] if prefetched_statuts else None
        else:
            statut = obj.statuts.order_by("-dateChangement").first()
        if statut:
            return {
                "id": statut.id,
                "statut": statut.statut,
                "dateChangement": statut.dateChangement,
            }
        return None

    def get_lieu(self, obj):
        if obj.lieu:
            return {"id": obj.lieu.id, "nomLieu": obj.lieu.nomLieu, "typeLieu": obj.lieu.typeLieu}
        return None

    class Meta:
        model = Equipement
        fields = "__all__"


class StatutEquipementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutEquipement
        fields = "__all__"


class ConstituerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constituer
        fields = "__all__"


class ModeleEquipementSerializer(serializers.ModelSerializer):
    fabricant = serializers.PrimaryKeyRelatedField(queryset=Fabricant.objects.all())

    class Meta:
        model = ModeleEquipement
        fields = "__all__"

    def to_representation(self, instance):
        """Renvoie le fabricant sous forme imbriquée en lecture."""
        data = super().to_representation(instance)
        if instance.fabricant:
            data["fabricant"] = FabricantSimpleSerializer(instance.fabricant).data
        return data


class CompteurSerializer(serializers.ModelSerializer):
    """Serializer complet pour un compteur avec option de niveau de détail"""

    seuils = serializers.SerializerMethodField()
    equipement_info = serializers.SerializerMethodField()

    class Meta:
        model = Compteur
        fields = "__all__"

    def get_equipement_info(self, obj):
        """Retourne les informations essentielles de l'équipement"""
        if obj.equipement:
            return {
                "id": obj.equipement.id,
                "designation": obj.equipement.designation,
                "numSerie": obj.equipement.numSerie,
                "reference": obj.equipement.reference,
                "lieu": {"id": obj.equipement.lieu.id, "nomLieu": obj.equipement.lieu.nomLieu}
                if obj.equipement.lieu
                else None,
            }
        return None

    def get_seuils(self, obj):
        """Retourne les seuils avec niveau de détail configurable"""
        request = self.context.get("request")
        detail_level = request.GET.get("detail", "lite") if request else "lite"

        seuils = obj.declenchements.all()

        if detail_level == "full":
            # Préchargement complet pour le niveau détaillé
            seuils = seuils.select_related(
                "planMaintenance__type_plan_maintenance"
            ).prefetch_related(
                "planMaintenance__planmaintenanceconsommable_set__consommable",
                "planMaintenance__planmaintenancedocument_set__document",
            )

        seuils_data = []
        for declencher in seuils:
            seuil_dict = {
                "id": declencher.id,
                "derniereIntervention": declencher.derniereIntervention,
                "prochaineMaintenance": declencher.prochaineMaintenance,
                "ecartInterventions": declencher.ecartInterventions,
                "estGlissant": declencher.estGlissant,
                "anticipationJours": declencher.anticipationJours,
                "planMaintenanceId": declencher.planMaintenance_id,
            }

            # Ajouter les détails du PM si demandé
            if declencher.planMaintenance:
                pm = declencher.planMaintenance
                seuil_dict["planMaintenance"] = {
                    "id": pm.id,
                    "nom": pm.nom,
                    "commentaire": pm.commentaire,
                    "type": pm.type_plan_maintenance.libelle if pm.type_plan_maintenance else None,
                    "type_id": pm.type_plan_maintenance_id,
                    "necessiteHabilitationElectrique": pm.necessiteHabilitationElectrique,
                    "necessitePermisFeu": pm.necessitePermisFeu,
                    "consommables": [
                        {
                            "id": rel.consommable.id,
                            "designation": rel.consommable.designation,
                            "quantite": rel.quantite_necessaire,
                        }
                        for rel in pm.planmaintenanceconsommable_set.all()
                    ],
                    "documents": [
                        {
                            "id": rel.document.id,
                            "nom": rel.document.nomDocument,
                            "chemin": rel.document.cheminAcces.name
                            if rel.document.cheminAcces
                            else None,
                            "type": rel.document.typeDocument.nomTypeDocument
                            if rel.document.typeDocument
                            else None,
                            "type_id": rel.document.typeDocument_id,
                        }
                        for rel in pm.planmaintenancedocument_set.all()
                    ],
                }

            seuils_data.append(seuil_dict)

        return seuils_data


class FamilleEquipementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilleEquipement
        fields = "__all__"


class EquipementCreateSerializer(serializers.ModelSerializer):
    createurEquipement = serializers.IntegerField()
    lieu = serializers.IntegerField()
    modeleEquipement = serializers.IntegerField(required=False, allow_null=True)
    fournisseur = serializers.IntegerField()
    fabricant = serializers.IntegerField()

    consommables = serializers.ListField(child=serializers.IntegerField(), required=False)
    compteurs = serializers.JSONField(required=False)

    lienImageEquipement = serializers.ImageField(required=False)

    class Meta:
        model = Equipement
        fields = [
            "reference",
            "designation",
            "dateCreation",
            "dateMiseEnService",
            "prixAchat",
            "createurEquipement",
            "lieu",
            "modeleEquipement",
            "fournisseur",
            "fabricant",
            "consommables",
            "numSerie",
            "compteurs",
            "lienImageEquipement",
            "type",
        ]


class EquipementAffichageSerializer(serializers.ModelSerializer):
    """Serializer pour l'affichage détaillé d'un équipement"""

    lieu = LieuSerializer(read_only=True)
    modele = ModeleEquipementSerializer(read_only=True)
    famille = serializers.SerializerMethodField()
    dernier_statut = serializers.SerializerMethodField()
    compteurs = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    documents_equipement = serializers.SerializerMethodField()
    consommables = serializers.SerializerMethodField()
    bons_travail = serializers.SerializerMethodField()
    fabricant = FabricantSimpleSerializer(read_only=True)
    fournisseur = FournisseurSimpleSerializer(read_only=True)
    createurEquipement = serializers.CharField(source="createurEquipement.nom", read_only=True)
    lienImage = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Equipement
        fields = [
            "id",
            "numSerie",
            "reference",
            "dateCreation",
            "designation",
            "type",
            "type_display",
            "dateMiseEnService",
            "prixAchat",
            "lienImage",
            "createurEquipement",
            "x",
            "y",
            "fabricant",
            "fournisseur",
            "lieu",
            "modele",
            "famille",
            "dernier_statut",
            "compteurs",
            "documents",
            "documents_equipement",
            "consommables",
            "bons_travail",
            "archive",
        ]

    def get_modele(self, obj):
        if obj.modele:
            return {
                "id": obj.modele.id,
                "nom": obj.modele.nom,
                "fabricant": {
                    "id": obj.modele.fabricant.id,
                    "nom": obj.modele.fabricant.nom,
                    "email": obj.modele.fabricant.email,
                }
                if obj.modele.fabricant
                else None,
            }
        return None

    def get_famille(self, obj):
        if obj.famille:
            return {"id": obj.famille.id, "nom": obj.famille.nom}
        return None

    def get_dernier_statut(self, obj):
        statut = obj.statuts.order_by("-dateChangement").first()
        if statut:
            return {
                "id": statut.id,
                "statut": statut.statut,
                "dateChangement": statut.dateChangement,
            }
        return None

    def get_compteurs(self, obj):
        """
        Retourne les compteurs d'un équipement avec leurs seuils et plans associés
        Chaque seuil peut avoir son propre plan de maintenance
        """
        request = self.context.get("request")
        seuils_lite = request and request.GET.get("seuils_lite", "false").lower() == "true"

        if seuils_lite:
            return self.get_compteurs_sans_seuils(obj)

        # Préchargement complet des données
        compteurs = obj.compteurs.all().prefetch_related(
            Prefetch(
                "declenchements",
                queryset=Declencher.objects.select_related(
                    "planMaintenance__type_plan_maintenance"
                ).prefetch_related(
                    "planMaintenance__planmaintenanceconsommable_set__consommable",
                    "planMaintenance__planmaintenancedocument_set__document",
                ),
            )
        )

        compteurs_data = []

        for c in compteurs:
            seuils_avec_plans = []

            # Pour chaque déclenchement (seuil)
            for declencher_relation in c.declenchements.all():
                plan_maintenance_info = None

                # Si ce seuil a un plan de maintenance associé
                if declencher_relation.planMaintenance:
                    plan_maintenance_obj = declencher_relation.planMaintenance

                    # Récupérer les consommables
                    consommables = []
                    for rel_conso in plan_maintenance_obj.planmaintenanceconsommable_set.all():
                        consommables.append(
                            {
                                "consommable": rel_conso.consommable.id,  # Format attendu par le frontend
                                "id": rel_conso.consommable.id,
                                "designation": rel_conso.consommable.designation,
                                "quantite": rel_conso.quantite_necessaire,
                            }
                        )

                    # Récupérer les documents
                    docs = []
                    for rel_doc in plan_maintenance_obj.planmaintenancedocument_set.all():
                        try:
                            path = (
                                rel_doc.document.cheminAcces.name
                                if rel_doc.document.cheminAcces
                                else None
                            )
                        except Exception:
                            path = None

                        docs.append(
                            {
                                "id": rel_doc.document.id,
                                "titre": rel_doc.document.nomDocument,
                                "path": path,
                                "type": rel_doc.document.typeDocument_id,
                            }
                        )

                    plan_maintenance_info = {
                        "id": plan_maintenance_obj.id,
                        "nom": plan_maintenance_obj.nom,
                        "commentaire": plan_maintenance_obj.commentaire,
                        "type": plan_maintenance_obj.type_plan_maintenance.libelle
                        if plan_maintenance_obj.type_plan_maintenance
                        else None,
                        "type_id": plan_maintenance_obj.type_plan_maintenance_id,
                        "necessiteHabilitationElectrique": plan_maintenance_obj.necessiteHabilitationElectrique,
                        "necessitePermisFeu": plan_maintenance_obj.necessitePermisFeu,
                        "consommables": consommables,
                        "documents": docs,
                    }

                # Créer l'objet seuil avec son plan associé
                seuil_object = {
                    "id": declencher_relation.id,
                    "derniereIntervention": declencher_relation.derniereIntervention,
                    "prochaineMaintenance": declencher_relation.prochaineMaintenance,
                    "ecartInterventions": declencher_relation.ecartInterventions,
                    "estGlissant": declencher_relation.estGlissant,
                    "planMaintenance": plan_maintenance_info,  # Plan spécifique à ce seuil
                }
                seuils_avec_plans.append(seuil_object)

            # Déterminer le plan de maintenance "principal" (pour compatibilité)
            plan_maintenance_principal = None
            seuil_principal = None
            if seuils_avec_plans and seuils_avec_plans[0].get("planMaintenance"):
                plan_maintenance_principal = seuils_avec_plans[0]["planMaintenance"]
                seuil_principal = seuils_avec_plans[0]

            compteur_dict = {
                "id": c.id,
                "nom": c.nomCompteur,
                "valeurCourante": c.valeurCourante,
                "unite": c.unite,
                "estPrincipal": c.estPrincipal,
                "type": c.type,
                # Champs du seuil (Declencher) pour compatibilité avec le frontend
                "derniereIntervention": seuil_principal["derniereIntervention"]
                if seuil_principal
                else 0,
                "intervalle": seuil_principal["ecartInterventions"] if seuil_principal else 0,
                "estGlissant": seuil_principal["estGlissant"] if seuil_principal else False,
                # Champs du plan de maintenance pour compatibilité
                "description": plan_maintenance_principal["commentaire"]
                if plan_maintenance_principal
                else "",
                "habElec": plan_maintenance_principal["necessiteHabilitationElectrique"]
                if plan_maintenance_principal
                else False,
                "permisFeu": plan_maintenance_principal["necessitePermisFeu"]
                if plan_maintenance_principal
                else False,
                # Structure complète
                "seuils": seuils_avec_plans,  # Tous les seuils avec leurs plans
                "seuil": seuils_avec_plans[0]
                if seuils_avec_plans
                else None,  # Premier seuil pour compatibilité
                "planMaintenance": plan_maintenance_principal,  # Plan principal (premier)
            }

            compteurs_data.append(compteur_dict)

        return compteurs_data

    def get_compteurs_sans_seuils(self, obj):
        """
        Retourne les compteurs d'un équipement avec uniquement les seuils (lite)
        Sans les plans de maintenance associés
        """
        compteurs = obj.compteurs.all()

        compteurs_data = []

        for c in compteurs:
            compteur_dict = {
                "id": c.id,
                "nom": c.nomCompteur,
                "valeurCourante": c.valeurCourante,
                "unite": c.unite,
                "estPrincipal": c.estPrincipal,
                "type": c.type,
            }

            compteurs_data.append(compteur_dict)

        return compteurs_data

    def get_documents(self, obj):
        docs_Pm = PlanMaintenance.objects.filter(equipement=obj).prefetch_related(
            "documents__typeDocument"
        )
        documents_list = []
        for pm in docs_Pm:
            for doc in pm.documents.all():
                try:
                    path = doc.cheminAcces.name if doc.cheminAcces else None
                except Exception:
                    path = None

                type_nom = doc.typeDocument.nomTypeDocument if doc.typeDocument else None

                documents_list.append(
                    {
                        "id": doc.id,
                        "titre": doc.nomDocument,
                        "path": path,
                        "type": doc.typeDocument_id,
                        "type_nom": type_nom,
                    }
                )
        return documents_list

    def get_documents_equipement(self, obj):
        """Retourne les documents directement liés à l'équipement"""
        documents_list = []
        for doc in obj.documents.all():
            try:
                path = doc.cheminAcces.name if doc.cheminAcces else None
            except Exception:
                path = None

            type_nom = doc.typeDocument.nomTypeDocument if doc.typeDocument else None

            documents_list.append(
                {
                    "id": doc.id,
                    "titre": doc.nomDocument,
                    "path": path,
                    "type": doc.typeDocument_id,
                    "type_nom": type_nom,
                }
            )
        return documents_list

    def get_consommables(self, obj):
        # Récupère tous les consommables liés à cet équipement
        relations = Constituer.objects.filter(equipement=obj).select_related("consommable")

        consommables_list = []
        for r in relations:
            consommable = r.consommable

            fabricant = consommable.fournitures.values_list("fabricant__nom", flat=True).first()

            consommables_list.append(
                {
                    "id": consommable.id,
                    "designation": consommable.designation,
                    "fabricant": fabricant if fabricant else None,
                }
            )

        return consommables_list

    def get_bons_travail(self, obj):
        bons = BonTravail.objects.filter(demande_intervention__equipement=obj).select_related(
            "responsable", "demande_intervention", "demande_intervention__equipement"
        )
        return [
            {
                "id": bon.id,
                "nom": bon.nom,
                "diagnostic": bon.diagnostic,
                "type": bon.type,
                "statut": bon.statut,
                "date_assignation": bon.date_assignation,
                "date_fin": bon.date_fin,
                "date_cloture": bon.date_cloture,
            }
            for bon in bons
        ]

    def get_lienImage(self, obj):
        """Retourne le nom du fichier ou l'URL complète"""
        if obj.lienImage:
            try:
                return obj.lienImage.name
            except Exception:
                return None
        return None


class DeclenchementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Declencher
        fields = "__all__"


class VehiculeProfileSerializer(serializers.ModelSerializer):
    """Champs spécifiques automobile d'un véhicule (cf. VehiculeProfile, ADR-001)."""

    class Meta:
        model = VehiculeProfile
        fields = ["vin", "immatriculation", "genre", "energie", "co2", "puissanceFiscale", "ptac"]


class VehiculeSerializer(EquipementSerializer):
    """Représentation en lecture d'un véhicule : champs Equipement + VehiculeProfile imbriqué."""

    vehicule_profile = VehiculeProfileSerializer(read_only=True)


class VehiculeCreateSerializer(EquipementCreateSerializer):
    """Payload de création d'un véhicule : champs Equipement + VehiculeProfile à plat.

    ``equipement.services.create_vehicule`` répartit ensuite ces champs
    entre l'``Equipement`` et le ``VehiculeProfile`` créés en une seule
    transaction (cf. TUS-005).
    """

    vin = serializers.RegexField(regex=r"^[A-HJ-NPR-Z0-9]{17}$")
    immatriculation = serializers.RegexField(regex=r"^[A-Z]{2}-\d{3}-[A-Z]{2}$")
    genre = serializers.ChoiceField(choices=VehiculeProfile.GENRE_CHOICES)
    energie = serializers.ChoiceField(choices=VehiculeProfile.ENERGIE_CHOICES)
    co2 = serializers.IntegerField(required=False, allow_null=True)
    puissanceFiscale = serializers.IntegerField(required=False, allow_null=True)
    ptac = serializers.IntegerField(required=False, allow_null=True)

    class Meta(EquipementCreateSerializer.Meta):
        fields = EquipementCreateSerializer.Meta.fields + [
            "vin",
            "immatriculation",
            "genre",
            "energie",
            "co2",
            "puissanceFiscale",
            "ptac",
        ]
