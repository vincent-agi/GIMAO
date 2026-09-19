from django.db import transaction
from django.db.models import Count, F, IntegerField, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from donnees.models import Adresse
from gimao.mixins import ArchivableViewSetMixin
from gimao.pagination import StandardPagination
from gimao.viewsets import GimaoModelViewSet
from stock.api.serializers import (
    ConsommableDetailSerializer,
    ConsommableSerializer,
    EstCompatibleSerializer,
    MagasinDetailSerializer,
    MagasinSerializer,
    PorterSurSerializer,
)
from stock.models import Consommable, EstCompatible, Magasin, PorterSur, Stocker


class MagasinViewSet(ArchivableViewSetMixin, GimaoModelViewSet):
    """ViewSet pour la gestion des magasins avec CRUD complet"""

    queryset = Magasin.objects.all()
    serializer_class = MagasinSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estMobile"]
    search_fields = ["nom"]
    ordering_fields = ["nom", "id"]
    ordering = ["nom"]

    def get_serializer_class(self):
        """Utilise le serializer détaillé pour les actions retrieve et list"""
        if self.action in ["retrieve", "list"]:
            return MagasinDetailSerializer
        return MagasinSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Création d'un magasin avec gestion de l'adresse imbriquée"""
        adresse_data = request.data.pop("adresse", None)
        if adresse_data:
            adresse = Adresse.objects.create(**adresse_data)
            request.data["adresse"] = adresse.id
        return super().create(request, *args, **kwargs)


class ConsommableViewSet(ArchivableViewSetMixin, GimaoModelViewSet):
    """ViewSet pour la gestion des consommables avec CRUD complet et filtrage par magasin"""

    queryset = Consommable.objects.all()
    serializer_class = ConsommableSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["magasins"]
    search_fields = ["designation", "stocks__magasin__nom"]
    ordering_fields = ["designation", "id", "seuilStockFaible"]
    ordering = ["designation"]

    def _get_detail_queryset(self):
        return Consommable.objects.prefetch_related(
            "magasins",
            "documents",
            Prefetch(
                "stocks",
                queryset=Stocker.objects.select_related("magasin").only(
                    "id",
                    "consommable_id",
                    "magasin_id",
                    "quantite",
                    "magasin__id",
                    "magasin__nom",
                ),
            ),
            Prefetch(
                "fournitures",
                queryset=PorterSur.objects.select_related("fournisseur", "fabricant").only(
                    "id",
                    "consommable_id",
                    "fournisseur_id",
                    "fabricant_id",
                    "quantite",
                    "prix_unitaire",
                    "date_reference_prix",
                    "fournisseur__id",
                    "fournisseur__nom",
                    "fabricant__id",
                    "fabricant__nom",
                ),
            ),
        )

    def _get_selected_stock_expression(self):
        magasin_id = self.request.query_params.get("magasin_id")
        if magasin_id and str(magasin_id).isdigit():
            return Coalesce(
                Sum(
                    "stocks__quantite",
                    filter=Q(stocks__magasin_id=int(magasin_id)),
                ),
                Value(0),
                output_field=IntegerField(),
            )

        return Coalesce(
            Sum("stocks__quantite"),
            Value(0),
            output_field=IntegerField(),
        )

    def get_queryset(self):
        queryset = self._get_detail_queryset()
        magasin_id = self.request.query_params.get("magasin_id")

        if magasin_id and str(magasin_id).isdigit():
            queryset = queryset.filter(stocks__magasin_id=int(magasin_id))

        queryset = queryset.annotate(filtered_quantite_totale=self._get_selected_stock_expression())

        stock_status = str(self.request.query_params.get("stock_status", "")).strip().lower()
        if stock_status == "hors-stock":
            queryset = queryset.filter(filtered_quantite_totale=0)
        elif stock_status == "sous-seuil":
            queryset = queryset.filter(
                filtered_quantite_totale__gt=0,
                seuilStockFaible__isnull=False,
                filtered_quantite_totale__lte=F("seuilStockFaible"),
            )
        elif stock_status == "stock-suffisant":
            queryset = queryset.exclude(
                Q(filtered_quantite_totale=0)
                | Q(
                    seuilStockFaible__isnull=False,
                    filtered_quantite_totale__lte=F("seuilStockFaible"),
                )
            )

        return queryset.distinct()

    def get_serializer_class(self):
        """Utilise le serializer détaillé pour les actions retrieve et list"""
        if self.action in ["retrieve", "list"]:
            return ConsommableDetailSerializer
        return ConsommableSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        summary = self._build_stock_summary(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response(
                {
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                    "summary": summary,
                }
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def _build_stock_summary(self, queryset):
        base_queryset = queryset.exclude(archive=True)
        return base_queryset.aggregate(
            hors_stock_count=Count(
                "id",
                filter=Q(filtered_quantite_totale=0),
                distinct=True,
            ),
            sous_seuil_count=Count(
                "id",
                filter=Q(
                    filtered_quantite_totale__gt=0,
                    seuilStockFaible__isnull=False,
                    filtered_quantite_totale__lte=F("seuilStockFaible"),
                ),
                distinct=True,
            ),
            stock_suffisant_count=Count(
                "id",
                filter=~(
                    Q(filtered_quantite_totale=0)
                    | Q(
                        seuilStockFaible__isnull=False,
                        filtered_quantite_totale__lte=F("seuilStockFaible"),
                    )
                ),
                distinct=True,
            ),
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def transfer_stock(self, request, pk=None):
        """Transférer du stock d'un magasin vers d'autres"""
        consommable = self.get_object()
        source_magasin_id = request.data.get("from_magasin")
        transfers = request.data.get("transfers", [])  # list of {to_magasin: id, quantite: int}

        if not source_magasin_id or not transfers:
            return Response({"error": "Données incomplètes"}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier stock source
        try:
            source_stock = Stocker.objects.get(
                consommable=consommable, magasin_id=source_magasin_id
            )
        except Stocker.DoesNotExist:
            return Response({"error": "Stock source introuvable"}, status=status.HTTP_404_NOT_FOUND)

        total_transfer = sum(t.get("quantite", 0) for t in transfers)

        if source_stock.quantite < total_transfer:
            return Response(
                {
                    "error": f"Stock insuffisant (Disponible: {source_stock.quantite}, Demandé: {total_transfer})"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Effectuer le transfert
        source_stock.quantite -= total_transfer
        source_stock.save()

        for transfer in transfers:
            to_magasin_id = transfer.get("to_magasin")
            quantite = transfer.get("quantite")

            if quantite > 0:
                dest_stock, created = Stocker.objects.get_or_create(
                    consommable=consommable, magasin_id=to_magasin_id, defaults={"quantite": 0}
                )
                dest_stock.quantite += quantite
                dest_stock.save()

        return Response({"status": "Transfert effectué"}, status=status.HTTP_200_OK)


class PorterSurViewSet(GimaoModelViewSet):
    """
    Historique des achats de consommables (une ligne par achat enregistré).

    Ce jeu de données croît avec chaque enregistrement d'achat ;
    la pagination évite de retourner l'intégralité de l'historique.
    Filtres disponibles : consommable, fournisseur, fabricant.
    """

    queryset = PorterSur.objects.select_related("consommable", "fournisseur", "fabricant").order_by(
        "-date_reference_prix"
    )
    serializer_class = PorterSurSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["consommable", "fournisseur", "fabricant"]
    ordering_fields = ["date_reference_prix", "prix_unitaire"]
    ordering = ["-date_reference_prix"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Créer un achat et distribuer le stock si demandé"""
        distribution_data = request.data.pop("distribution", [])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase = serializer.save()

        if distribution_data:
            total_distributed = sum(item.get("quantite", 0) for item in distribution_data)
            if total_distributed != purchase.quantite:
                # Rollback handled by transaction.atomic if we raise exception
                # But here we just want to return strict error before proceeding?
                # Actually, raising exception acts as rollback.
                raise serializers.ValidationError(
                    {
                        "distribution": f"La quantité distribuée ({total_distributed}) ne correspond pas à la quantité achetée ({purchase.quantite})."
                    }
                )

            for item in distribution_data:
                magasin_id = item.get("magasin")
                quantite = item.get("quantite")
                if quantite > 0:
                    stock, created = Stocker.objects.get_or_create(
                        consommable=purchase.consommable,
                        magasin_id=magasin_id,
                        defaults={"quantite": 0},
                    )
                    stock.quantite += quantite
                    stock.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class EstCompatibleViewSet(GimaoModelViewSet):
    """ViewSet pour la gestion de la compatibilité consommable-modèle"""

    queryset = EstCompatible.objects.all()
    serializer_class = EstCompatibleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["consommable", "modeleEquipement"]
