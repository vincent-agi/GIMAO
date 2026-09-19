from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from donnees.api.serializers import (
    FabricantSimpleSerializer,
    FournisseurSimpleSerializer,
    TypeDocumentSerializer,
)
from donnees.models import Fabricant, Fournisseur, Lieu, TypeDocument
from equipement.api.serializers import (
    FamilleEquipementSerializer,
    ModeleEquipementSerializer,
)
from equipement.models import FamilleEquipement, ModeleEquipement
from gimao.pagination import LargePagination
from maintenance.api.serializers import TypePlanMaintenanceSerializer
from maintenance.models import TypePlanMaintenance
from stock.api.serializers import ConsommableSerializer
from stock.models import Consommable


class EquipementFormDataPagination(LargePagination):
    pass


class EquipementFormDataView(APIView):
    """
    Endpoint unique pour récupérer toutes les données nécessaires à la création d'un équipement.
    Réduit 8 requêtes API en une seule pour améliorer les performances (Green IT).

    GET /api/equipements/form-data/
    """

    SECTION_CONFIG = {
        "equipmentModels": {
            "queryset": ModeleEquipement.objects.select_related("fabricant").all(),
            "serializer": ModeleEquipementSerializer,
            "search_field": "nom",
            "ordering": "nom",
        },
        "fabricants": {
            "queryset": Fabricant.objects.all(),
            "serializer": FabricantSimpleSerializer,
            "search_field": "nom",
            "ordering": "nom",
        },
        "fournisseurs": {
            "queryset": Fournisseur.objects.all(),
            "serializer": FournisseurSimpleSerializer,
            "search_field": "nom",
            "ordering": "nom",
        },
        "consumables": {
            "queryset": Consommable.objects.prefetch_related("magasins", "documents"),
            "serializer": ConsommableSerializer,
            "search_field": "designation",
            "ordering": "designation",
        },
        "familles": {
            "queryset": FamilleEquipement.objects.all(),
            "serializer": FamilleEquipementSerializer,
            "search_field": "nom",
            "ordering": "nom",
        },
        "typesPM": {
            "queryset": TypePlanMaintenance.objects.all(),
            "serializer": TypePlanMaintenanceSerializer,
            "search_field": "libelle",
            "ordering": "libelle",
        },
        "typesDocuments": {
            "queryset": TypeDocument.objects.all(),
            "serializer": TypeDocumentSerializer,
            "search_field": "nomTypeDocument",
            "ordering": "nomTypeDocument",
        },
    }

    def _is_truthy(self, value):
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _build_locations_tree(self):
        lieux = list(Lieu.objects.all().order_by("nomLieu"))
        children_by_parent = {}

        for lieu in lieux:
            children_by_parent.setdefault(lieu.lieuParent_id, []).append(lieu)

        def build_node(lieu):
            return {
                "id": lieu.id,
                "nomLieu": lieu.nomLieu,
                "children": [build_node(child) for child in children_by_parent.get(lieu.id, [])],
            }

        return [build_node(racine) for racine in children_by_parent.get(None, [])]

    def _get_section_response(self, request, section):
        config = self.SECTION_CONFIG.get(section)
        if config is None:
            return Response(
                {"error": f"Section inconnue: {section}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = config["queryset"].order_by(config["ordering"])

        ids = request.query_params.get("ids")
        if ids:
            selected_ids = [int(value) for value in ids.split(",") if value.strip().isdigit()]
            if selected_ids:
                queryset = queryset.filter(id__in=selected_ids)

        search = str(request.query_params.get("search", "")).strip()
        if search:
            queryset = queryset.filter(**{f"{config['search_field']}__icontains": search})

        paginator = EquipementFormDataPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = config["serializer"](page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def get(self, request):
        try:
            section = request.query_params.get("section")
            if section:
                return self._get_section_response(request, section)

            response_data = {
                "locations": self._build_locations_tree(),
                "familles": FamilleEquipementSerializer(
                    FamilleEquipement.objects.all().order_by("nom"),
                    many=True,
                ).data,
                "typesPM": TypePlanMaintenanceSerializer(
                    TypePlanMaintenance.objects.all().order_by("libelle"),
                    many=True,
                ).data,
                "typesDocuments": TypeDocumentSerializer(
                    TypeDocument.objects.all().order_by("nomTypeDocument"),
                    many=True,
                ).data,
            }

            if not self._is_truthy(request.query_params.get("minimal")):
                response_data.update(
                    {
                        "equipmentModels": ModeleEquipementSerializer(
                            ModeleEquipement.objects.select_related("fabricant")
                            .all()
                            .order_by("nom"),
                            many=True,
                        ).data,
                        "fabricants": FabricantSimpleSerializer(
                            Fabricant.objects.all().order_by("nom"),
                            many=True,
                        ).data,
                        "fournisseurs": FournisseurSimpleSerializer(
                            Fournisseur.objects.all().order_by("nom"),
                            many=True,
                        ).data,
                        "consumables": ConsommableSerializer(
                            Consommable.objects.prefetch_related("magasins", "documents")
                            .all()
                            .order_by("designation"),
                            many=True,
                        ).data,
                    }
                )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "error": "Erreur lors de la récupération des données",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
