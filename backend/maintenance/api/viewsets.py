import ast
import json
import logging
import os
import re
import traceback
from urllib.parse import parse_qs

from django.db import transaction
from django.db.models import Count, F, Prefetch, Q
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from donnees.models import Document
from equipement.models import Equipement, StatutEquipement
from gimao.mixins import ArchivableViewSetMixin
from gimao.pagination import PaginatedActionMixin, StandardPagination
from gimao.viewsets import GimaoModelViewSet
from maintenance.api.serializers import (
    BonTravailDetailSerializer,
    BonTravailListStockSerializer,
    BonTravailSerializer,
    DemandeInterventionDetailSerializer,
    DemandeInterventionSerializer,
    PlanMaintenanceConsommableSerializer,
    PlanMaintenanceSerializer,
    TypePlanMaintenanceSerializer,
)
from maintenance.models import (
    BonTravail,
    BonTravailConsommable,
    BonTravailConsommableReservation,
    BonTravailDocument,
    DemandeIntervention,
    DemandeInterventionDocument,
    PlanMaintenance,
    PlanMaintenanceConsommable,
    PlanMaintenanceDocument,
    TypePlanMaintenance,
)
from stock.models import Stocker
from utilisateur.models import Log, Utilisateur

logger = logging.getLogger(__name__)


class DemandeInterventionViewSet(PaginatedActionMixin, ArchivableViewSetMixin, GimaoModelViewSet):
    """
    ViewSet pour gérer les demandes d'intervention.

    Liste des endpoints:
    - GET /demandes-intervention/ : Liste toutes les demandes
    - POST /demandes-intervention/ : Crée une nouvelle demande
    - GET /demandes-intervention/{id}/ : Détail d'une demande
    - PUT/PATCH /demandes-intervention/{id}/ : Modifie une demande
    - DELETE /demandes-intervention/{id}/ : Supprime une demande
    - GET /demandes-intervention/en_attente/ : Demandes non traitées
    - GET /demandes-intervention/traitees/ : Demandes traitées
    - GET /demandes-intervention/par_equipement/?equipement_id=X : Filtre par équipement
    - POST /demandes-intervention/{id}/traiter/ : Marque comme traitée
    """

    queryset = DemandeIntervention.objects.all()
    serializer_class = DemandeInterventionSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "nom",
        "commentaire",
        "utilisateur__nomUtilisateur",
        "utilisateur__prenom",
        "utilisateur__nomFamille",
        "equipement__designation",
        "equipement__reference",
    ]
    ordering_fields = ["id", "nom", "date_creation", "date_changementStatut", "statut"]
    ordering = ["-date_creation", "-id"]

    def _get_list_queryset(self):
        return DemandeIntervention.objects.select_related(
            "utilisateur",
            "equipement",
            "equipement__lieu",
        ).prefetch_related(
            Prefetch(
                "equipement__statuts",
                queryset=StatutEquipement.objects.only(
                    "id",
                    "statut",
                    "dateChangement",
                    "equipement_id",
                ).order_by("-dateChangement"),
                to_attr="prefetched_statuts",
            ),
        )

    def _get_detail_queryset(self):
        return self._get_list_queryset().prefetch_related(
            Prefetch(
                "documents",
                queryset=Document.objects.select_related("typeDocument").only(
                    "id",
                    "nomDocument",
                    "cheminAcces",
                    "typeDocument_id",
                    "typeDocument__id",
                    "typeDocument__nomTypeDocument",
                ),
            ),
        )

    def get_queryset(self):
        if self.action == "retrieve":
            return self._get_detail_queryset()

        queryset = self._get_list_queryset()

        if self.action == "list":
            vue = str(self.request.query_params.get("vue", "")).strip().lower()
            if vue == "ancien":
                # Anciennes DI : transformées (en BT) ou rejetées
                queryset = queryset.filter(statut__in=["TRANSFORMEE", "REFUSEE"])
            elif vue == "tout":
                # Toutes les DI, quel que soit leur statut
                pass
            else:
                # Vue par défaut : DI actives (en attente ou acceptées)
                queryset = queryset.filter(statut__in=["EN_ATTENTE", "ACCEPTEE"])

        return queryset

    def _parse_json_field(self, data, key, default):
        raw = data.get(key, default)
        if raw is None:
            return default
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except ValueError:
                return default
        return raw

    def get_serializer_class(self):
        """Utilise le serializer détaillé pour retrieve"""
        if self.action == "retrieve":
            return DemandeInterventionDetailSerializer
        return DemandeInterventionSerializer

    @action(detail=False, methods=["get"])
    def en_attente(self, request):
        """Retourne les demandes d'intervention en attente de traitement"""
        demandes = self.get_queryset().filter(date_traitement__isnull=True)
        serializer = self.get_serializer(demandes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def traitees(self, request):
        """Retourne les demandes d'intervention traitées"""
        demandes = self.get_queryset().filter(date_traitement__isnull=False)
        serializer = self.get_serializer(demandes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def par_equipement(self, request):
        """
        Filtre les demandes par équipement
        Query param: equipement_id
        """
        equipement_id = request.query_params.get("equipement_id")
        if not equipement_id:
            return Response(
                {"error": "Le paramètre equipement_id est requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        demandes = self.filter_queryset(self.get_queryset().filter(equipement_id=equipement_id))
        return self.get_paginated_response_for_queryset(demandes)

    @action(detail=False, methods=["get"])
    def par_utilisateur(self, request):
        """
        Filtre les demandes par utilisateur
        Query param: utilisateur_id
        """
        utilisateur_id = request.query_params.get("utilisateur_id")
        if not utilisateur_id:
            return Response(
                {"error": "Le paramètre utilisateur_id est requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        demandes = self.filter_queryset(self.get_queryset().filter(utilisateur_id=utilisateur_id))
        return self.get_paginated_response_for_queryset(demandes)

    @action(detail=True, methods=["post"])
    def traiter(self, request, pk=None):
        """Marque une demande comme traitée"""
        demande = self.get_object()
        demande.date_traitement = timezone.now()
        demande.save()
        serializer = self.get_serializer(demande)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def updateStatus(self, request, pk=None):
        """Met à jour le statut d'une DI et horodate le changement. Body : { "statut": "ACCEPTEE" }"""
        demande = self.get_object()
        demande.statut = request.data.get("statut", demande.statut)
        demande.date_changementStatut = timezone.now()
        demande.save()
        serializer = self.get_serializer(demande)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def delink_document(self, request, pk=None):
        """Délie un document d'une demande d'intervention."""
        demande = self.get_object()
        document_id = request.data.get("document_id")

        if not document_id:
            document_id = request.query_params.get("document_id")

        if not document_id:
            return Response(
                {"error": "Le paramètre document_id est requis"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Vérification si le document est bien lié à la demande
        if not demande.documents.filter(id=document_id).exists():
            return Response(
                {"error": "Ce document n'est pas lié à cette demande"},
                status=status.HTTP_404_NOT_FOUND,
            )

        demande.documents.remove(document_id)

        # On utilise le serializer détaillé pour renvoyer la liste des documents mise à jour
        serializer = DemandeInterventionDetailSerializer(demande, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def ajouter_document(self, request, pk=None):
        """Lie un document existant à une demande d'intervention.

        Payload attendu:
        - document_id: id du Document
        """
        demande = self.get_object()

        document_id = request.data.get("document_id") or request.query_params.get("document_id")
        if not document_id:
            return Response(
                {"error": "Le champ document_id est requis."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            document_id = int(document_id)
        except Exception:
            return Response(
                {"error": "document_id doit être un entier."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not Document.objects.filter(id=document_id).exists():
            return Response({"error": "Document introuvable."}, status=status.HTTP_400_BAD_REQUEST)

        if demande.documents.filter(id=document_id).exists():
            serializer = DemandeInterventionDetailSerializer(demande, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        list(demande.documents.order_by("id").values_list("id", flat=True))
        demande.documents.add(document_id)
        list(demande.documents.order_by("id").values_list("id", flat=True))

        serializer = DemandeInterventionDetailSerializer(demande, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def transform_to_bon_travail(self, request, *args, **kwargs):
        """Transforme une demande d'intervention en bon de travail."""
        demande = self.get_object()
        print(demande, request.data.get("responsable"))
        diagnostic = (request.data.get("diagnostic") or "").strip()

        # Création du bon de travail
        bon_travail = BonTravail.objects.create(
            demande_intervention=demande,
            nom=demande.nom,
            type="CORRECTIF",
            diagnostic=diagnostic,
            commentaire=demande.commentaire,
            responsable_id=request.data.get("responsable"),
            statut="EN_ATTENTE",
        )

        statut_equipement = request.data.get("statut_equipement")
        if statut_equipement and statut_equipement.strip():
            from equipement.models import StatutEquipement

            StatutEquipement.objects.create(equipement=demande.equipement, statut=statut_equipement)

        demande.statut = "TRANSFORMEE"
        demande.date_changementStatut = timezone.now()
        demande.save()
        serializer = BonTravailSerializer(bon_travail, context=self.get_serializer_context())
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Création d'une nouvelle demande d'intervention"""
        data = dict(request.data)

        # Extraire les valeurs uniques des listes
        for key, value in data.items():
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        # Validation serializer
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Récupération de l'utilisateur
        utilisateur_id = data.get("utilisateur_id")
        utilisateur = None
        if utilisateur_id:
            try:
                utilisateur = Utilisateur.objects.get(id=utilisateur_id)
            except (Utilisateur.DoesNotExist, ValueError):
                pass

        if not utilisateur and request.user.is_authenticated:
            utilisateur = request.user

        if not utilisateur:
            return Response(
                {"error": "Utilisateur non identifié"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Récupération de l'équipement
        equipement_id = data.get("equipement_id")
        try:
            equipement = Equipement.objects.get(id=equipement_id)
        except Equipement.DoesNotExist:
            return Response({"error": "Équipement invalide"}, status=status.HTTP_400_BAD_REQUEST)

        # Création de la demande
        demande = DemandeIntervention.objects.create(
            nom=data["nom"],
            commentaire=data.get("commentaire", ""),
            statut="EN_ATTENTE",
            statut_suppose=data.get("statut_suppose"),
            date_creation=timezone.now(),
            date_changementStatut=timezone.now(),
            utilisateur=utilisateur,
            equipement=equipement,
        )

        # Gestion des documents (transactionnelle et stricte)
        documents_data = self._parse_json_field(data, "documents", [])
        if documents_data is None:
            documents_data = []
        if not isinstance(documents_data, list):
            raise ValidationError({"documents": "Format invalide (liste attendue)"})

        created_files = []
        try:
            for index, doc_data in enumerate(documents_data):
                if not doc_data:
                    continue
                if not isinstance(doc_data, dict):
                    raise ValidationError({"documents": f"Document #{index}: format invalide"})

                type_doc_id = doc_data.get("typeDocument_id")
                nom_doc = doc_data.get("nomDocument")

                uploaded_file = request.FILES.get(f"document_{index}")
                if not uploaded_file:
                    file_obj = doc_data.get("cheminAcces")
                    if hasattr(file_obj, "read"):
                        uploaded_file = file_obj

                is_empty = not type_doc_id and not (nom_doc or "").strip() and not uploaded_file
                if is_empty:
                    continue

                # Nouveau document => type + fichier requis
                if not type_doc_id:
                    raise ValidationError(
                        {"documents": f"Document #{index}: typeDocument_id requis"}
                    )
                if not uploaded_file:
                    raise ValidationError(
                        {"documents": f"Document #{index}: fichier manquant (document_{index})"}
                    )

                document = Document.objects.create(
                    nomDocument=(nom_doc or uploaded_file.name),
                    cheminAcces=uploaded_file,
                    typeDocument_id=type_doc_id,
                )
                created_files.append(document.cheminAcces.name)

                DemandeInterventionDocument.objects.create(
                    demande_intervention=demande,
                    document=document,
                )

        except Exception:
            # Best-effort: si des fichiers ont été sauvegardés avant l'erreur, tenter de les supprimer
            for name in reversed(created_files):
                try:
                    if name:
                        Document._meta.get_field("cheminAcces").storage.delete(name)
                except Exception:
                    pass
            raise

        return Response(DemandeInterventionSerializer(demande).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """PATCH /demandes-intervention/{id}/ avec gestion transactionnelle des documents."""
        instance = self.get_object()

        data = dict(request.data)
        for key, value in list(data.items()):
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        documents_in_payload = ("documents" in request.data) or any(
            k.startswith("document_") for k in request.FILES.keys()
        )
        documents_data = []
        if documents_in_payload:
            documents_data = self._parse_json_field(data, "documents", [])
            if documents_data is None:
                documents_data = []
            if not isinstance(documents_data, list):
                raise ValidationError({"documents": "Format invalide (liste attendue)"})

        new_file_names_to_delete_on_error = []
        old_file_names_to_delete_on_commit = []

        # 1) Mise à jour DI via serializer
        di_payload = {}
        allowed_fields = [
            "nom",
            "commentaire",
            "statut",
            "statut_suppose",
            "equipement_id",
            "utilisateur_id",
        ]
        for f in allowed_fields:
            if f in data:
                di_payload[f] = data.get(f)

        if di_payload:
            serializer = self.get_serializer(instance, data=di_payload, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        # Reload after DI save
        demande_apres = DemandeIntervention.objects.get(pk=instance.pk)

        try:
            # 2) Documents: update / create + link
            if documents_in_payload:
                for index, doc_data in enumerate(documents_data):
                    if not doc_data:
                        continue
                    if not isinstance(doc_data, dict):
                        raise ValidationError({"documents": f"Document #{index}: format invalide"})

                    doc_id_raw = doc_data.get("document_id")
                    type_doc_id = doc_data.get("typeDocument_id")
                    nom_doc = doc_data.get("nomDocument")

                    uploaded_file = request.FILES.get(f"document_{index}")
                    if not uploaded_file:
                        file_obj = doc_data.get("cheminAcces")
                        if hasattr(file_obj, "read"):
                            uploaded_file = file_obj

                    is_empty = (
                        not doc_id_raw
                        and not type_doc_id
                        and not (nom_doc or "").strip()
                        and not uploaded_file
                    )
                    if is_empty:
                        continue

                    # Update d'un document existant
                    if doc_id_raw:
                        try:
                            doc_id = int(doc_id_raw)
                        except Exception:
                            raise ValidationError(
                                {"documents": f"Document #{index}: document_id invalide"}
                            ) from None

                        try:
                            document = Document.objects.get(id=doc_id)
                        except Document.DoesNotExist:
                            raise ValidationError(
                                {"documents": f"Document #{index}: document introuvable"}
                            ) from None

                        has_changes = False
                        if nom_doc is not None and str(nom_doc) != (document.nomDocument or ""):
                            document.nomDocument = str(nom_doc)
                            has_changes = True
                        if type_doc_id is not None and str(type_doc_id) != str(
                            document.typeDocument_id or ""
                        ):
                            document.typeDocument_id = type_doc_id
                            has_changes = True

                        if uploaded_file is not None:
                            old_name = getattr(document.cheminAcces, "name", None)
                            document.cheminAcces = uploaded_file
                            has_changes = True
                            if old_name:
                                old_file_names_to_delete_on_commit.append(old_name)

                        if has_changes:
                            document.save()
                            new_name = getattr(document.cheminAcces, "name", None)
                            if uploaded_file is not None and new_name:
                                new_file_names_to_delete_on_error.append(new_name)

                        # S'assurer que le lien existe
                        DemandeInterventionDocument.objects.get_or_create(
                            demande_intervention=demande_apres,
                            document=document,
                        )
                        continue

                    # Nouveau document
                    if not type_doc_id:
                        raise ValidationError(
                            {"documents": f"Document #{index}: typeDocument_id requis"}
                        )
                    if not uploaded_file:
                        raise ValidationError(
                            {"documents": f"Document #{index}: fichier manquant (document_{index})"}
                        )

                    document = Document.objects.create(
                        nomDocument=(nom_doc or uploaded_file.name),
                        cheminAcces=uploaded_file,
                        typeDocument_id=type_doc_id,
                    )
                    new_name = getattr(document.cheminAcces, "name", None)
                    if new_name:
                        new_file_names_to_delete_on_error.append(new_name)

                    DemandeInterventionDocument.objects.create(
                        demande_intervention=demande_apres,
                        document=document,
                    )

            # Supprimer les anciens fichiers uniquement après commit
            if old_file_names_to_delete_on_commit:
                storage = Document._meta.get_field("cheminAcces").storage
                for name in old_file_names_to_delete_on_commit:

                    def _delete_old(n=name):
                        try:
                            storage.delete(n)
                        except Exception:
                            pass

                    transaction.on_commit(_delete_old)

            serializer = self.get_serializer(demande_apres)
            return Response(serializer.data)

        except Exception:
            storage = Document._meta.get_field("cheminAcces").storage
            for name in reversed(new_file_names_to_delete_on_error):
                try:
                    if name:
                        storage.delete(name)
                except Exception:
                    pass
            raise


class BonTravailViewSet(PaginatedActionMixin, ArchivableViewSetMixin, GimaoModelViewSet):
    """
    ViewSet pour gérer les bons de travail.

    Liste des endpoints:
    - GET /bons-travail/ : Liste tous les bons
    - POST /bons-travail/ : Crée un nouveau bon
    - GET /bons-travail/{id}/ : Détail d'un bon
    - PUT/PATCH /bons-travail/{id}/ : Modifie un bon
    - DELETE /bons-travail/{id}/ : Supprime un bon
    - PATCH /bons-travail/{id}/updateStatus/ : Change le statut
    - PATCH /bons-travail/{id}/delink_document/ : Délie un document du bon
    """

    queryset = BonTravail.objects.all()
    serializer_class = BonTravailSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "nom",
        "diagnostic",
        "commentaire",
        "demande_intervention__equipement__designation",
        "demande_intervention__equipement__reference",
        "responsable__prenom",
        "responsable__nomFamille",
        "utilisateur_assigne__prenom",
        "utilisateur_assigne__nomFamille",
        "bontravailconsommable__consommable__designation",
    ]
    ordering_fields = ["id", "nom", "date_assignation", "date_prevue", "date_cloture", "statut"]
    ordering = ["-date_assignation", "-id"]

    def _prefetched_assignees(self):
        return Prefetch(
            "utilisateur_assigne",
            queryset=Utilisateur.objects.only(
                "id",
                "nomUtilisateur",
                "email",
                "prenom",
                "nomFamille",
                "photoProfil",
            ).order_by("id"),
        )

    def _prefetched_documents(self, relation):
        return Prefetch(
            relation,
            queryset=Document.objects.select_related("typeDocument")
            .only(
                "id",
                "nomDocument",
                "cheminAcces",
                "typeDocument_id",
                "typeDocument__id",
                "typeDocument__nomTypeDocument",
            )
            .order_by("id"),
        )

    def _prefetched_statuts(self):
        return Prefetch(
            "demande_intervention__equipement__statuts",
            queryset=StatutEquipement.objects.only(
                "id",
                "statut",
                "dateChangement",
                "equipement_id",
            ).order_by("-dateChangement"),
            to_attr="prefetched_statuts",
        )

    def _get_base_queryset(self):
        return BonTravail.objects.select_related(
            "demande_intervention",
            "demande_intervention__utilisateur",
            "demande_intervention__equipement",
            "demande_intervention__equipement__lieu",
            "responsable",
        )

    def _get_list_queryset(self):
        return self._get_base_queryset().prefetch_related(
            self._prefetched_assignees(),
        )

    def _get_detail_queryset(self):
        return self._get_base_queryset().prefetch_related(
            self._prefetched_assignees(),
            self._prefetched_documents("documents"),
            self._prefetched_documents("demande_intervention__documents"),
            self._prefetched_statuts(),
            Prefetch(
                "bontravailconsommable_set",
                queryset=BonTravailConsommable.objects.select_related("consommable").only(
                    "id",
                    "bon_travail_id",
                    "consommable_id",
                    "quantite_utilisee",
                    "consommable__id",
                    "consommable__designation",
                    "consommable__lienImageConsommable",
                ),
                to_attr="prefetched_consommables",
            ),
        )

    def _get_list_stock_queryset(self):
        return self._get_base_queryset().prefetch_related(
            self._prefetched_assignees(),
            self._prefetched_documents("documents"),
            self._prefetched_documents("demande_intervention__documents"),
            self._prefetched_statuts(),
            Prefetch(
                "bontravailconsommable_set",
                queryset=BonTravailConsommable.objects.select_related("consommable")
                .only(
                    "id",
                    "bon_travail_id",
                    "consommable_id",
                    "quantite_utilisee",
                    "estConfirme",
                    "date_confirme",
                    "magasin_reserve_id",
                    "consommable__id",
                    "consommable__designation",
                    "consommable__lienImageConsommable",
                )
                .prefetch_related(
                    Prefetch(
                        "reservations",
                        queryset=BonTravailConsommableReservation.objects.select_related(
                            "magasin"
                        ).only(
                            "id",
                            "bon_travail_consommable_id",
                            "magasin_id",
                            "quantite",
                            "magasin__id",
                            "magasin__nom",
                        ),
                    ),
                    Prefetch(
                        "consommable__stocks",
                        queryset=Stocker.objects.select_related("magasin").only(
                            "id",
                            "consommable_id",
                            "magasin_id",
                            "quantite",
                            "magasin__id",
                            "magasin__nom",
                        ),
                    ),
                ),
                to_attr="prefetched_consommables",
            ),
        )

    def _create_log_entry(
        self, type_action, nom_table, id_cible, champs_modifies, utilisateur_id=None
    ):
        try:
            utilisateur = None
            if utilisateur_id:
                try:
                    utilisateur = Utilisateur.objects.get(pk=utilisateur_id)
                except (Utilisateur.DoesNotExist, ValueError, TypeError):
                    utilisateur = None

            Log.objects.create(
                type=type_action,
                nomTable=nom_table,
                idCible=id_cible,
                champsModifies=champs_modifies,
                utilisateur=utilisateur,
            )
        except Exception as error:
            print(f"Erreur lors de la creation du log manuel: {error}")

    def _get_consommables_state(self, bon_travail_id):
        return list(
            BonTravailConsommable.objects.filter(bon_travail_id=bon_travail_id)
            .order_by("consommable_id")
            .values("consommable_id", "quantite_utilisee")
        )

    def _get_documents_state(self, bon_travail_id):
        return list(
            BonTravailDocument.objects.filter(bon_travail_id=bon_travail_id)
            .order_by("document_id")
            .values_list("document_id", flat=True)
        )

    def _get_utilisateur_assigne_ids(self, bon):
        return list(bon.utilisateur_assigne.order_by("id").values_list("id", flat=True))

    def _normalize_id_list(self, raw):
        if raw is None:
            return []

        if isinstance(raw, (list, tuple)):
            values = raw
        else:
            values = [raw]

        ids = []
        for v in values:
            try:
                i = int(v)
            except Exception:
                continue
            if i > 0:
                ids.append(i)

        # dédoublonne en conservant l'ordre
        seen = set()
        out = []
        for i in ids:
            if i in seen:
                continue
            seen.add(i)
            out.append(i)
        return out

    def _sync_consommables_from_request(self, bon, request_data):
        # Supporte deux formats :
        # - consommables: [{consommable_id, quantite_utilisee}]
        # - consommables_ids: [id, id]
        if "consommables" not in request_data and "consommables_ids" not in request_data:
            return

        consommables_dict = {}
        raw_lines = request_data.get("consommables")
        raw_ids = request_data.get("consommables_ids")

        if isinstance(raw_lines, (list, tuple)):
            for line in raw_lines:
                if not isinstance(line, dict):
                    continue
                cid = line.get("consommable_id")
                if cid is None or cid == "":
                    continue
                try:
                    cid = int(cid)
                except Exception:
                    continue
                if cid <= 0:
                    continue

                q = line.get("quantite_utilisee", 0)
                try:
                    q = int(q)
                except Exception:
                    q = 0
                consommables_dict[cid] = max(0, q)

        elif isinstance(raw_ids, (list, tuple)):
            for cid in raw_ids:
                try:
                    cid = int(cid)
                except Exception:
                    continue
                if cid <= 0:
                    continue
                consommables_dict[cid] = 0

        ids = set(consommables_dict.keys())

        BonTravailConsommable.objects.filter(bon_travail=bon).exclude(
            consommable_id__in=ids
        ).delete()

        for consommable_id, quantite in consommables_dict.items():
            BonTravailConsommable.objects.update_or_create(
                bon_travail=bon,
                consommable_id=consommable_id,
                defaults={"quantite_utilisee": quantite},
            )

    def get_serializer_class(self):
        """Utilise le serializer détaillé pour retrieve"""
        if self.action == "retrieve":
            return BonTravailDetailSerializer
        return BonTravailSerializer

    def get_queryset(self):
        """Par défaut, on n'affiche pas les BT clôturés.

        Query param: cloture (optionnel)
        - cloture=true (ou 1) => inclut les BT au statut CLOTURE
        """
        if self.action == "list_stock":
            queryset = self._get_list_stock_queryset()
        elif self.action == "retrieve":
            queryset = self._get_detail_queryset()
        else:
            queryset = self._get_list_queryset()

        queryset = queryset.distinct()

        statut = str(self.request.query_params.get("statut", "")).strip().upper()
        if statut and statut != "ALL":
            queryset = queryset.filter(statut=statut)

        if getattr(self, "action", None) not in {"list", "assigne_a"}:
            return queryset

        queryset = queryset.filter(archive=False)

        # Vue "ancien" : afficher uniquement les BT terminés ou clôturés
        vue = str(self.request.query_params.get("vue", "")).strip().lower()
        if vue == "ancien":
            return queryset.filter(statut__in=["TERMINE", "CLOTURE"])

        # Vue "tout" : tous les BT, quel que soit leur statut
        if vue == "tout":
            return queryset

        # Si un statut précis est demandé, on respecte ce choix (déjà filtré plus haut)
        if statut and statut != "ALL":
            return queryset

        cloture_raw = str(self.request.query_params.get("cloture", "false")).strip().lower()
        include_cloture = cloture_raw in ["true", "1"]
        if include_cloture:
            return queryset

        # Vue par défaut (actifs) : on masque les terminés et clôturés
        return queryset.exclude(statut__in=["TERMINE", "CLOTURE"])

    def filter_queryset(self, queryset):
        """Recherche par numéro de BT (ex: "BT-0004", "4") en plus de la recherche texte."""
        search = str(self.request.query_params.get("search", "")).strip()
        match = re.match(r"^(?:BT-?)?0*(\d+)$", search, re.IGNORECASE)
        if match:
            return queryset.filter(id=int(match.group(1)))
        return super().filter_queryset(queryset)

    def _parse_json_field(self, data, key, default):
        raw = data.get(key, default)
        if raw is None:
            return default
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except ValueError:
                return default
        return raw

    @action(
        detail=False,
        methods=["post"],
        url_path="create_with_di",
        parser_classes=[MultiPartParser, FormParser, JSONParser],
    )
    @transaction.atomic
    def create_with_di(self, request, *args, **kwargs):
        """Crée une DemandeIntervention + BonTravail + Documents dans une transaction.

        Objectif: si un document échoue, rien n'est créé/modifié.

        Payload (multipart recommandé):
        - Champs DI: nom, commentaire, equipement_id, utilisateur_id
        - Champs BT: type, date_prevue, diagnostic, responsable_id, utilisateur_assigne_ids, consommables
        - Documents: documents = JSON list[{nomDocument,typeDocument_id}] + fichiers document_0, document_1, ...
        """
        data = dict(request.data)

        # Extraire les valeurs uniques des listes (ne pas casser les champs "list" attendus)
        list_fields = {
            "utilisateur_assigne_ids",
            "consommables_ids",
        }
        for key, value in list(data.items()):
            if key in list_fields:
                continue
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        # Utilisateur
        utilisateur_id = data.get("utilisateur_id") or data.get("user")
        utilisateur = None
        if utilisateur_id:
            try:
                utilisateur = Utilisateur.objects.get(id=utilisateur_id)
            except (Utilisateur.DoesNotExist, ValueError):
                utilisateur = None
        if not utilisateur and request.user.is_authenticated:
            utilisateur = request.user
        if not utilisateur:
            raise ValidationError({"utilisateur_id": "Utilisateur non identifié"})

        # Équipement
        equipement_id = data.get("equipement_id")
        try:
            equipement = Equipement.objects.get(id=equipement_id)
        except (Equipement.DoesNotExist, ValueError, TypeError):
            raise ValidationError({"equipement_id": "Équipement invalide"}) from None

        # Documents (metadata)
        documents_data = self._parse_json_field(data, "documents", [])
        if documents_data is None:
            documents_data = []
        if not isinstance(documents_data, list):
            raise ValidationError({"documents": "Format invalide (liste attendue)"})

        created_files = []  # best-effort cleanup si exception (FieldFile names)

        try:
            # Créer DI (directement au statut TRANSFORMEE car on crée le BT dans la même action)
            demande = DemandeIntervention.objects.create(
                nom=data.get("nom") or "",
                commentaire=data.get("commentaire", ""),
                statut="TRANSFORMEE",
                statut_suppose=data.get("statut_suppose")
                or data.get("statut_equipement")
                or "EN_FONCTIONNEMENT",
                date_creation=timezone.now(),
                date_changementStatut=timezone.now(),
                utilisateur=utilisateur,
                equipement=equipement,
            )
            if not demande.nom:
                raise ValidationError({"nom": "Le nom est requis"})
            print(
                "Statut : "
                + str(demande.statut)
                + " - Statut supposé : "
                + str(demande.statut_suppose)
            )
            if demande.statut_suppose:
                StatutEquipement.objects.create(
                    equipement=equipement,
                    statut=demande.statut_suppose,
                    dateChangement=timezone.now(),
                )

            # Créer BT via serializer (validation + sync consommables)
            bt_payload = {
                "demande_intervention": demande.id,
                "nom": data.get("nom") or demande.nom,
                "type": data.get("type") or "CORRECTIF",
                "date_prevue": data.get("date_prevue") or None,
                "commentaire": data.get("commentaire", ""),
                "diagnostic": data.get("diagnostic", ""),
                # Responsable obligatoire: l'utilisateur qui crée le BT
                "responsable_id": utilisateur.id,
            }

            duree = data.get("duree_previsionnelle")

            if duree:
                # Si format HH:MM → on ajoute les secondes
                if len(duree.split(":")) == 2:
                    duree = f"{duree}:00"

            bt_payload["duree_previsionnelle"] = duree

            # Champs optionnels (responsable non modifiable ici)
            if "utilisateur_assigne_ids" in data:
                bt_payload["utilisateur_assigne_ids"] = data.get("utilisateur_assigne_ids")

            consommables = self._parse_json_field(data, "consommables", None)
            if consommables is not None:
                bt_payload["consommables"] = consommables

            bt_serializer = BonTravailSerializer(data=bt_payload)
            bt_serializer.is_valid(raise_exception=True)
            bon = bt_serializer.save()

            # Assigner date_assignation si des techniciens sont présents
            if bon.date_assignation is None and bon.utilisateur_assigne.exists():
                bon.date_assignation = timezone.now()
                bon.save(update_fields=["date_assignation"])

            # Lier documents au BT (et créer les documents)
            for index, doc_data in enumerate(documents_data):
                if not doc_data:
                    continue
                if not isinstance(doc_data, dict):
                    raise ValidationError({"documents": f"Document #{index}: format invalide"})

                type_doc_id = doc_data.get("typeDocument_id")
                if not type_doc_id:
                    raise ValidationError(
                        {"documents": f"Document #{index}: typeDocument_id requis"}
                    )

                uploaded_file = request.FILES.get(f"document_{index}")
                if not uploaded_file:
                    file_obj = doc_data.get("cheminAcces")
                    if hasattr(file_obj, "read"):
                        uploaded_file = file_obj

                if not uploaded_file:
                    raise ValidationError(
                        {"documents": f"Document #{index}: fichier manquant (document_{index})"}
                    )

                document = Document.objects.create(
                    nomDocument=doc_data.get("nomDocument") or uploaded_file.name,
                    cheminAcces=uploaded_file,
                    typeDocument_id=type_doc_id,
                )
                created_files.append(document.cheminAcces.name)

                BonTravailDocument.objects.create(
                    bon_travail=bon,
                    document=document,
                )

            # Refresh pour cohérence réponse
            bon.refresh_from_db()
            response_data = BonTravailDetailSerializer(bon, context={"request": request}).data

            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception:
            # Best-effort: si des fichiers ont été sauvegardés avant l'erreur, tenter de les supprimer
            print(
                "Exception détectée, tentative de cleanup des fichiers créés...Exception:",
                traceback.format_exc(),
            )
            for name in reversed(created_files):
                try:
                    if name:
                        Document._meta.get_field("cheminAcces").storage.delete(name)
                except Exception:
                    pass
            raise

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Création d'un bon de travail.

        - Supporte date_prevue lors de la création.
        - Si des techniciens sont assignés (utilisateur_assigne_ids), date_assignation = now.
        - Logue la création au format demandé.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bon = serializer.save()

        # Si des techniciens sont assignés => date_assignation = now
        if bon.date_assignation is None and bon.utilisateur_assigne.exists():
            bon.date_assignation = timezone.now()
            bon.save(update_fields=["date_assignation"])

        # Force refresh from DB pour que toutes les relations soient à jour
        bon.refresh_from_db()

        response_serializer = self.get_serializer(bon)
        bon_data = response_serializer.data

        return Response(bon_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"])
    @transaction.atomic
    def updateStatus(self, request, pk=None):
        """Endpoint unique pour gérer les changements de statut d'un bon de travail.

        Payload attendu: {"statut": "EN_COURS"|"TERMINE"|"CLOTURE"|...}
        - EN_COURS (démarrer): date_debut = now
        - TERMINE (terminer): date_fin = now
        - CLOTURE (clôturer): date_cloture = now (et date_fin si manquante)
        """
        bon = self.get_object()
        new_statut = request.data.get("statut")
        if not new_statut:
            return Response(
                {"error": "Le champ statut est requis"}, status=status.HTTP_400_BAD_REQUEST
            )

        request.data.get("user")

        BonTravail.objects.get(pk=bon.pk)

        # Règles spécifiques
        if new_statut == "EN_COURS":
            # Deux cas :
            # - Démarrage: EN_ATTENTE/EN_RETARD -> EN_COURS (date_debut = now)
            # - Refus de clôture: TERMINE -> EN_COURS (date_fin = null + commentaire_refus_cloture)
            if bon.statut in ["EN_ATTENTE", "EN_RETARD"]:
                bon.statut = "EN_COURS"
                bon.date_debut = timezone.now()
            elif bon.statut == "TERMINE":
                commentaire_refus_cloture = request.data.get("commentaire_refus_cloture")
                if not commentaire_refus_cloture or not str(commentaire_refus_cloture).strip():
                    return Response(
                        {"error": "Le commentaire de refus de clôture est requis"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                bon.statut = "EN_COURS"
                bon.date_fin = None
                bon.date_cloture = None
                bon.commentaire_refus_cloture = str(commentaire_refus_cloture).strip()
            else:
                return Response(
                    {
                        "error": "Le bon doit être en attente, en retard ou terminé pour passer en cours"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif new_statut == "TERMINE":
            # Terminer l'intervention (date_fin = now)
            if bon.statut != "EN_COURS":
                return Response(
                    {"error": "Le bon doit être en cours pour être terminé"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            bon.statut = "TERMINE"
            bon.date_fin = timezone.now()
        elif new_statut == "CLOTURE":
            # Clôturer le bon de travail
            bon.statut = "CLOTURE"
            bon.date_cloture = timezone.now()
            if not bon.date_fin:
                bon.date_fin = timezone.now()
        else:
            bon.statut = new_statut

        bon.save()

        serializer = self.get_serializer(bon)
        return Response(serializer.data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """PATCH /bons-travail/{id}/

        - Interdit de modifier la DI (et donc l'équipement).
        - Logue une entre 'modification' avec uniquement les champs réellement modifiés.
        """
        forbidden_fields = {
            "demande_intervention",
            "demande_intervention_id",
            "equipement",
            "equipement_id",
        }
        for key in forbidden_fields:
            if key in request.data:
                return Response(
                    {
                        "error": "Modification de la demande d'intervention / équipement interdite via un BT"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        instance = self.get_object()
        bon_avant = BonTravail.objects.get(pk=instance.pk)

        data = dict(request.data)
        list_fields = {
            "utilisateur_assigne_ids",
            "consommables_ids",
        }
        for key, value in list(data.items()):
            if key in list_fields:
                continue
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        (
            data.get("user")
            or data.get("utilisateur_id")
            or (
                request.user.id
                if getattr(request, "user", None) and request.user.is_authenticated
                else None
            )
        )

        # Snapshot avant la mise à jour (sinon on relit l'état "après" et on ne détecte rien)
        avant_assigne_ids = list(bon_avant.utilisateur_assigne.values_list("id", flat=True))
        self._get_consommables_state(bon_avant.id)
        self._get_documents_state(bon_avant.id)

        documents_in_payload = ("documents" in request.data) or any(
            k.startswith("document_") for k in request.FILES.keys()
        )
        documents_data = []
        if documents_in_payload:
            documents_data = self._parse_json_field(data, "documents", [])
            if documents_data is None:
                documents_data = []
            if not isinstance(documents_data, list):
                raise ValidationError({"documents": "Format invalide (liste attendue)"})

        # Best-effort cleanup fichiers uploadés pendant cette requête (si erreur)
        new_file_names_to_delete_on_error = []
        old_file_names_to_delete_on_commit = []

        # 1) Mise à jour BT via serializer (validation + sync consommables)
        bt_payload = {}
        allowed_fields = [
            "nom",
            "diagnostic",
            "type",
            "date_assignation",
            "date_prevue",
            "duree_previsionnelle",
            "date_cloture",
            "date_debut",
            "date_fin",
            "statut",
            "commentaire",
            "commentaire_refus_cloture",
            "responsable_id",
            "utilisateur_assigne_ids",
            "consommables",
            "consommables_ids",
        ]
        for f in allowed_fields:
            if f not in data:
                continue
            v = data.get(f)
            if f == "date_prevue" and (v is None or str(v) == ""):
                bt_payload[f] = None
            else:
                bt_payload[f] = v

        consommables = self._parse_json_field(data, "consommables", None)
        if consommables is not None:
            bt_payload["consommables"] = consommables

        # Statut d'équipement
        print(data)
        nouveau_statut = data.get("statut_equipement")
        if nouveau_statut is not None:
            equipement = (
                Equipement.objects.filter(id=data.get("equipement_id")).first()
                or instance.demande_intervention.equipement
            )
            dernier_statut_eq = equipement.get_dernier_statut()

            if dernier_statut_eq is None or dernier_statut_eq != nouveau_statut:
                StatutEquipement.objects.create(
                    equipement=equipement, statut=nouveau_statut, dateChangement=timezone.now()
                )
                bt_payload["statut_equipement"] = nouveau_statut

        if bt_payload:
            # Normaliser le cas multipart (FormData) :
            # - valeurs reçues en str
            # - suppression => utilisateur_assigne_ids='' ou ['']
            if "utilisateur_assigne_ids" in bt_payload:
                raw = bt_payload.get("utilisateur_assigne_ids")
                if raw is None or raw == "":
                    bt_payload["utilisateur_assigne_ids"] = []
                else:
                    if isinstance(raw, str):
                        raw_values = [raw]
                    elif isinstance(raw, (list, tuple)):
                        raw_values = list(raw)
                    else:
                        raw_values = [raw]

                    ids = []
                    for v in raw_values:
                        if v is None or v == "":
                            continue
                        try:
                            ids.append(int(v))
                        except Exception:
                            continue
                    bt_payload["utilisateur_assigne_ids"] = ids

            serializer = self.get_serializer(instance, data=bt_payload, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        # Recharger l'instance après sauvegarde
        bon_apres = BonTravail.objects.get(pk=instance.pk)

        try:
            # 2) Documents (création / mise à jour + lien)
            if documents_in_payload:
                for index, doc_data in enumerate(documents_data):
                    if not doc_data:
                        continue
                    if not isinstance(doc_data, dict):
                        raise ValidationError({"documents": f"Document #{index}: format invalide"})

                    doc_id_raw = doc_data.get("document_id")
                    type_doc_id = doc_data.get("typeDocument_id")
                    nom_doc = doc_data.get("nomDocument")

                    uploaded_file = request.FILES.get(f"document_{index}")
                    if not uploaded_file:
                        file_obj = doc_data.get("cheminAcces")
                        if hasattr(file_obj, "read"):
                            uploaded_file = file_obj

                    # Ligne vide ?
                    is_empty = (
                        not doc_id_raw
                        and not type_doc_id
                        and not (nom_doc or "").strip()
                        and not uploaded_file
                    )
                    if is_empty:
                        continue

                    if doc_id_raw:
                        try:
                            doc_id = int(doc_id_raw)
                        except Exception:
                            raise ValidationError(
                                {"documents": f"Document #{index}: document_id invalide"}
                            ) from None

                        try:
                            document = Document.objects.get(id=doc_id)
                        except Document.DoesNotExist:
                            raise ValidationError(
                                {"documents": f"Document #{index}: document introuvable"}
                            ) from None

                        {
                            "nomDocument": document.nomDocument,
                            "typeDocument_id": document.typeDocument_id,
                            "cheminAcces": getattr(document.cheminAcces, "name", None),
                        }

                        has_changes = False
                        if nom_doc is not None and str(nom_doc) != (document.nomDocument or ""):
                            document.nomDocument = str(nom_doc)
                            has_changes = True
                        if type_doc_id is not None and str(type_doc_id) != str(
                            document.typeDocument_id or ""
                        ):
                            document.typeDocument_id = type_doc_id
                            has_changes = True

                        if uploaded_file is not None:
                            old_name = getattr(document.cheminAcces, "name", None)
                            document.cheminAcces = uploaded_file
                            has_changes = True
                            if old_name:
                                old_file_names_to_delete_on_commit.append(old_name)

                        if has_changes:
                            document.save()
                            new_name = getattr(document.cheminAcces, "name", None)
                            if uploaded_file is not None and new_name:
                                new_file_names_to_delete_on_error.append(new_name)

                        continue

                    # Nouveau document
                    if not type_doc_id:
                        raise ValidationError(
                            {"documents": f"Document #{index}: typeDocument_id requis"}
                        )
                    if not uploaded_file:
                        raise ValidationError(
                            {"documents": f"Document #{index}: fichier manquant (document_{index})"}
                        )

                    document = Document.objects.create(
                        nomDocument=(nom_doc or uploaded_file.name),
                        cheminAcces=uploaded_file,
                        typeDocument_id=type_doc_id,
                    )
                    new_name = getattr(document.cheminAcces, "name", None)
                    if new_name:
                        new_file_names_to_delete_on_error.append(new_name)

                    BonTravailDocument.objects.create(bon_travail=bon_apres, document=document)

            # Supprimer les anciens fichiers uniquement après commit
            if old_file_names_to_delete_on_commit:
                storage = Document._meta.get_field("cheminAcces").storage
                for name in old_file_names_to_delete_on_commit:

                    def _delete_old(n=name):
                        try:
                            storage.delete(n)
                        except Exception:
                            pass

                    transaction.on_commit(_delete_old)

            # Recharger après documents
            bon_apres = BonTravail.objects.get(pk=instance.pk)

            if "utilisateur_assigne_ids" in data:
                avant_ids = avant_assigne_ids
                apres_ids = list(bon_apres.utilisateur_assigne.values_list("id", flat=True))
                if sorted(avant_ids) != sorted(apres_ids):
                    # Si on change les assignés, on (re)met la date d'assignation à maintenant
                    # (uniquement si au moins un assigné est présent après la modif)
                    if bon_apres.utilisateur_assigne.exists():
                        bon_apres.date_assignation = timezone.now()
                        bon_apres.save(update_fields=["date_assignation"])
                        # Recharge pour garantir l'état DB (et avoir la valeur exacte renvoyée)
                        bon_apres = BonTravail.objects.get(pk=instance.pk)

            serializer = self.get_serializer(bon_apres)
            return Response(serializer.data)

        except Exception:
            storage = Document._meta.get_field("cheminAcces").storage
            for name in reversed(new_file_names_to_delete_on_error):
                try:
                    if name:
                        storage.delete(name)
                except Exception:
                    pass
            raise

    @action(detail=False, methods=["get"])
    def assigne_a(self, request, pk=None):
        """Retourne la liste des BT assignés à un utilisateur."""
        user = request.query_params.get("utilisateur_id")
        if not user:
            return Response(
                {"error": "Le paramètre utilisateur_id est requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bons = self.filter_queryset(self.get_queryset().filter(utilisateur_assigne__id=user))
        return self.get_paginated_response_for_queryset(bons)

    @action(detail=True, methods=["patch"])
    def delink_document(self, request, pk=None):
        bon = self.get_object()
        document_id = request.data.get("document_id")

        if not document_id:
            document_id = request.query_params.get("document_id")

        if not document_id:
            return Response(
                {"error": "Le paramètre document_id est requis"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not bon.documents.filter(id=document_id).exists():
            return Response(
                {"error": "Ce document n'est pas lié à ce bon"}, status=status.HTTP_404_NOT_FOUND
            )

        bon.documents.remove(document_id)

        serializer = BonTravailDetailSerializer(bon, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def ajouter_document(self, request, pk=None):
        """Lie un document existant au BT.

        Payload attendu:
        - document_id: id du Document
        """
        bon = self.get_object()

        document_id = request.data.get("document_id")
        if not document_id:
            return Response(
                {"error": "Le champ document_id est requis."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            document_id = int(document_id)
        except Exception:
            return Response(
                {"error": "document_id doit être un entier."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not Document.objects.filter(id=document_id).exists():
            return Response({"error": "Document introuvable."}, status=status.HTTP_400_BAD_REQUEST)

        if bon.documents.filter(id=document_id).exists():
            serializer = BonTravailDetailSerializer(bon, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        self._get_documents_state(bon.id)
        bon.documents.add(document_id)
        self._get_documents_state(bon.id)

        serializer = BonTravailDetailSerializer(bon, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def list_stock(self, request):
        """Liste tous les BonTravail non CLOTURE et non TERMINE avec leurs consommables.

        Endpoint idéal pour le magasinier pour voir les BT en cours et les consommables à distribuer.
        """
        queryset = self.get_queryset().exclude(statut__in=["CLOTURE", "TERMINE"]).distinct()

        queryset = self._with_list_stock_counts(self.filter_queryset(queryset))
        summary = self._build_list_stock_summary(queryset)
        queryset = self._apply_list_stock_state_filter(queryset)

        return self.get_paginated_response_for_queryset(
            queryset,
            serializer_class=BonTravailListStockSerializer,
            extra={"summary": summary},
        )

    def _with_list_stock_counts(self, queryset):
        return queryset.annotate(
            total_consommables_count=Count("bontravailconsommable", distinct=True),
            confirmed_consommables_count=Count(
                "bontravailconsommable",
                filter=Q(bontravailconsommable__estConfirme=True),
                distinct=True,
            ),
        )

    def _build_list_stock_summary(self, queryset):
        return queryset.aggregate(
            pending_count=Count(
                "id",
                filter=Q(
                    total_consommables_count__gt=0,
                    confirmed_consommables_count__lt=F("total_consommables_count"),
                    pieces_recuperees=False,
                ),
                distinct=True,
            ),
            reserved_count=Count(
                "id",
                filter=Q(
                    total_consommables_count__gt=0,
                    confirmed_consommables_count=F("total_consommables_count"),
                    pieces_recuperees=False,
                ),
                distinct=True,
            ),
            recovered_count=Count(
                "id",
                filter=Q(pieces_recuperees=True),
                distinct=True,
            ),
        )

    def _apply_list_stock_state_filter(self, queryset):
        reservation_state = (
            str(self.request.query_params.get("reservation_state", "")).strip().lower()
        )

        if reservation_state == "pending":
            return queryset.filter(
                total_consommables_count__gt=0,
                confirmed_consommables_count__lt=F("total_consommables_count"),
                pieces_recuperees=False,
            )

        if reservation_state == "reserved":
            return queryset.filter(
                total_consommables_count__gt=0,
                confirmed_consommables_count=F("total_consommables_count"),
                pieces_recuperees=False,
            )

        if reservation_state == "recovered":
            return queryset.filter(pieces_recuperees=True)

        return queryset

    def _serialize_reservations(self, assoc):
        return [
            {
                "magasin_id": reservation.magasin_id,
                "magasin_nom": reservation.magasin.nom,
                "quantite": reservation.quantite,
            }
            for reservation in assoc.reservations.select_related("magasin").all()
        ]

    def _restore_reservations(self, assoc):
        reservations = list(assoc.reservations.select_related("magasin").all())

        if reservations:
            for reservation in reservations:
                stock, _ = Stocker.objects.get_or_create(
                    consommable_id=assoc.consommable_id,
                    magasin_id=reservation.magasin_id,
                    defaults={"quantite": 0},
                )
                stock.quantite += int(reservation.quantite or 0)
                stock.save(update_fields=["quantite"])

            assoc.reservations.all().delete()
            return

        if assoc.magasin_reserve_id and assoc.quantite_utilisee:
            try:
                stock = Stocker.objects.get(
                    consommable_id=assoc.consommable_id, magasin_id=assoc.magasin_reserve_id
                )
                stock.quantite += int(assoc.quantite_utilisee or 0)
                stock.save(update_fields=["quantite"])
            except Stocker.DoesNotExist:
                pass

    def _build_insufficient_stock_response(
        self, assoc, needed, stocks, error_message="Stock insuffisant"
    ):
        total_available = sum(int(stock.quantite or 0) for stock in stocks)

        return Response(
            {
                "error": error_message,
                "insuffisants": [
                    {
                        "consommable_id": assoc.consommable_id,
                        "designation": assoc.consommable.designation,
                        "needed": needed,
                        "available": total_available,
                        "stocks": [
                            {
                                "magasin_id": stock.magasin_id,
                                "magasin_nom": stock.magasin.nom,
                                "quantite": stock.quantite,
                            }
                            for stock in stocks
                        ],
                    }
                ],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _normalize_repartition(self, repartition):
        current = repartition

        for _ in range(6):
            if current is None:
                return None

            if isinstance(current, bytes):
                try:
                    current = current.decode("utf-8")
                except UnicodeDecodeError:
                    return None
                continue

            if isinstance(current, dict):
                return [current]

            if isinstance(current, tuple):
                current = list(current)
                continue

            if isinstance(current, list):
                if len(current) == 1 and isinstance(current[0], str):
                    current = current[0]
                    continue
                return current

            if isinstance(current, str):
                current = current.strip()
                if not current:
                    return None

                if len(current) >= 2 and current[0] == current[-1] and current[0] in ("'", '"'):
                    current = current[1:-1].strip()
                    continue

                for parser in (json.loads, ast.literal_eval):
                    try:
                        current = parser(current)
                        break
                    except (ValueError, SyntaxError, TypeError):
                        continue
                else:
                    unescaped = current.replace('\\"', '"').replace("\\'", "'")
                    if unescaped != current:
                        current = unescaped
                        continue
                    return None
                continue

            return None

        return current if isinstance(current, list) else None

    def _extract_repartition(self, request):
        candidates = []

        raw_request = getattr(request, "_request", None)
        for source in (
            getattr(request, "data", None),
            getattr(request, "POST", None),
            getattr(raw_request, "POST", None),
        ):
            if source is None:
                continue
            try:
                has_repartition = "repartition" in source
            except TypeError:
                has_repartition = False
            getter = getattr(source, "get", None)
            if callable(getter):
                value = getter("repartition")
                if value is not None:
                    candidates.append(value)
            getlist = getattr(source, "getlist", None)
            if callable(getlist) and has_repartition:
                values = getlist("repartition")
                if values:
                    candidates.append(values)

        try:
            raw_body = request.body.decode("utf-8").strip()
        except Exception:
            raw_body = ""

        if raw_body:
            try:
                body_json = json.loads(raw_body)
            except ValueError:
                body_json = None

            if isinstance(body_json, dict):
                if "repartition" in body_json:
                    candidates.append(body_json.get("repartition"))
            elif isinstance(body_json, list):
                candidates.append(body_json)

            parsed_body = parse_qs(raw_body, keep_blank_values=True)
            if "repartition" in parsed_body:
                candidates.append(parsed_body.get("repartition"))

        for candidate in candidates:
            normalized = self._normalize_repartition(candidate)
            if normalized is not None:
                return normalized

        return None

    def _apply_reservation_split(self, assoc, needed, repartition):
        if not isinstance(repartition, list) or len(repartition) == 0:
            return Response(
                {"error": "La repartition des magasins est invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if assoc.estConfirme:
            self._restore_reservations(assoc)

        total_selected = 0
        seen_magasins = set()
        stock_updates = []

        for item in repartition:
            magasin_id = item.get("magasin_id", item.get("magasin"))
            quantite = item.get("quantite")

            try:
                magasin_id = int(magasin_id)
                quantite = int(quantite)
            except (TypeError, ValueError):
                return Response(
                    {
                        "error": "Chaque ligne de repartition doit contenir un magasin_id et une quantite entiers."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if quantite <= 0:
                return Response(
                    {"error": "Chaque quantite de repartition doit etre strictement positive."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if magasin_id in seen_magasins:
                return Response(
                    {
                        "error": "Un magasin ne peut etre present qu une seule fois dans la repartition."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            stock = (
                Stocker.objects.select_related("magasin")
                .filter(consommable_id=assoc.consommable_id, magasin_id=magasin_id)
                .first()
            )
            if stock is None:
                return Response(
                    {"error": "Stock introuvable pour un des magasins selectionnes."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if stock.quantite < quantite:
                return Response(
                    {
                        "error": "Stock insuffisant",
                        "insuffisants": [
                            {
                                "consommable_id": assoc.consommable_id,
                                "designation": assoc.consommable.designation,
                                "needed": quantite,
                                "available": stock.quantite,
                                "magasin_id": stock.magasin_id,
                                "magasin_nom": stock.magasin.nom,
                            }
                        ],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            seen_magasins.add(magasin_id)
            total_selected += quantite
            stock_updates.append((stock, quantite))

        if total_selected != needed:
            return Response(
                {"error": f"La repartition doit totaliser exactement {needed}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assoc.reservations.all().delete()
        reservations = []

        for stock, quantite in stock_updates:
            stock.quantite -= quantite
            stock.save(update_fields=["quantite"])
            reservations.append(
                BonTravailConsommableReservation(
                    bon_travail_consommable=assoc, magasin_id=stock.magasin_id, quantite=quantite
                )
            )

        BonTravailConsommableReservation.objects.bulk_create(reservations)
        assoc.magasin_reserve_id = (
            stock_updates[0][0].magasin_id if len(stock_updates) == 1 else None
        )

        return None

    @action(detail=True, methods=["patch"])
    @transaction.atomic
    def update_consommable_distribution(self, request, pk=None):
        bon = self.get_object()
        consommable_id = request.data.get("consommable_id")
        distribue = request.data.get("distribue", False)
        magasin_id = request.data.get("magasin_id")
        repartition = self._extract_repartition(request)
        logger.warning(
            "update_consommable_distribution bt=%s consommable=%s magasin_id=%s raw_repartition=%r normalized_repartition=%r content_type=%s",
            pk,
            consommable_id,
            magasin_id,
            request.data.get("repartition", None),
            repartition,
            request.content_type,
        )

        if not consommable_id:
            return Response({"error": "consommable_id requis"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assoc = BonTravailConsommable.objects.get(
                bon_travail=bon, consommable_id=consommable_id
            )
        except BonTravailConsommable.DoesNotExist:
            return Response(
                {"error": "Consommable non trouvé pour ce BT"}, status=status.HTTP_404_NOT_FOUND
            )

        if distribue:
            needed = int(assoc.quantite_utilisee or 0)
            if needed <= 0:
                return Response(
                    {
                        "error": "Quantite non renseignee pour ce consommable.",
                        "insuffisants": [
                            {
                                "consommable_id": assoc.consommable_id,
                                "designation": assoc.consommable.designation,
                                "needed": needed,
                                "available": 0,
                            }
                        ],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if repartition is not None:
                error_response = self._apply_reservation_split(assoc, needed, repartition)
                if error_response is not None:
                    return error_response

                assoc.estConfirme = True
                assoc.date_confirme = timezone.now()
                assoc.save()

                return JsonResponse(
                    {
                        "consommable_id": assoc.consommable_id,
                        "distribue": assoc.estConfirme,
                        "date_distribution": assoc.date_confirme.isoformat()
                        if assoc.date_confirme
                        else None,
                        "magasin_reserve": assoc.magasin_reserve_id,
                        "magasins_reserves": self._serialize_reservations(assoc),
                    }
                )

            if needed > 0:
                if magasin_id:
                    try:
                        stock = Stocker.objects.get(
                            consommable_id=consommable_id, magasin_id=magasin_id
                        )
                    except Stocker.DoesNotExist:
                        return Response(
                            {"error": "Stock introuvable pour ce magasin"},
                            status=status.HTTP_404_NOT_FOUND,
                        )
                    if stock.quantite < needed:
                        return Response(
                            {
                                "error": "Stock insuffisant",
                                "insuffisants": [
                                    {
                                        "consommable_id": assoc.consommable_id,
                                        "designation": assoc.consommable.designation,
                                        "needed": needed,
                                        "available": stock.quantite,
                                        "magasin_id": stock.magasin_id,
                                        "magasin_nom": stock.magasin.nom,
                                    }
                                ],
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    stock.quantite -= needed
                    stock.save()
                    assoc.magasin_reserve_id = int(magasin_id)
                else:
                    all_stocks = list(
                        Stocker.objects.select_related("magasin").filter(
                            consommable_id=consommable_id
                        )
                    )
                    eligible = [stock for stock in all_stocks if stock.quantite >= needed]
                    if len(eligible) == 0:
                        total_available = sum(int(stock.quantite or 0) for stock in all_stocks)
                        stocks = [
                            {
                                "magasin_id": stock.magasin_id,
                                "magasin__nom": stock.magasin.nom,
                                "quantite": stock.quantite,
                            }
                            for stock in all_stocks
                        ]
                        error_message = "Stock insuffisant"
                        if total_available >= needed and total_available > 0:
                            error_message = "Le stock existe mais il est réparti sur plusieurs magasins. Aucun magasin ne couvre seul la quantité demandée."
                        return Response(
                            {
                                "error": error_message,
                                "insuffisants": [
                                    {
                                        "consommable_id": assoc.consommable_id,
                                        "designation": assoc.consommable.designation,
                                        "needed": needed,
                                        "available": total_available,
                                        "stocks": stocks,
                                    }
                                ],
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if len(eligible) > 1:
                        magasins = [
                            {"id": s.magasin_id, "nom": s.magasin.nom, "quantite": s.quantite}
                            for s in eligible
                        ]
                        return Response(
                            {
                                "error": "Selection magasin requise",
                                "needs_magasin_selection": True,
                                "magasins": magasins,
                            },
                            status=status.HTTP_409_CONFLICT,
                        )
                    stock = eligible[0]
                    stock.quantite -= needed
                    stock.save()
                    assoc.magasin_reserve_id = stock.magasin_id

            assoc.estConfirme = True
            assoc.date_confirme = timezone.now()
        else:
            self._restore_reservations(assoc)
            assoc.estConfirme = False
            assoc.date_confirme = None
            assoc.magasin_reserve = None
        assoc.save()

        return JsonResponse(
            {
                "consommable_id": assoc.consommable_id,
                "distribue": assoc.estConfirme,
                "date_distribution": assoc.date_confirme.isoformat()
                if assoc.date_confirme
                else None,
                "magasin_reserve": assoc.magasin_reserve_id,
                "magasins_reserves": self._serialize_reservations(assoc),
            }
        )

    @action(detail=True, methods=["patch"])
    @transaction.atomic
    def cancel_mise_de_cote(self, request, pk=None):
        bon = self.get_object()

        assocs = BonTravailConsommable.objects.filter(bon_travail=bon)
        for assoc in assocs:
            self._restore_reservations(assoc)
            assoc.estConfirme = False
            assoc.date_confirme = None
            assoc.magasin_reserve = None
            assoc.save()

        return JsonResponse({"ok": True})

    @action(detail=True, methods=["patch"])
    @transaction.atomic
    def set_recupere(self, request, pk=None):
        bon = self.get_object()
        recupere = request.data.get("recupere", True)

        bon.pieces_recuperees = bool(recupere)
        bon.date_recuperation = timezone.now() if bon.pieces_recuperees else None
        bon.save(update_fields=["pieces_recuperees", "date_recuperation"])

        return JsonResponse(
            {
                "pieces_recuperees": bon.pieces_recuperees,
                "date_recuperation": bon.date_recuperation.isoformat()
                if bon.date_recuperation
                else None,
            }
        )

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        queryset = (
            self.get_queryset()
            .select_related("demande_intervention__equipement")
            .prefetch_related("utilisateur_assigne")
            .filter(date_prevue__isnull=False, statut__in=["EN_ATTENTE", "EN_COURS", "EN_RETARD"])
        )
        bts = queryset.order_by("duree_previsionnelle")
        data = []
        for bt in bts:
            start = bt.date_prevue
            end = (
                (bt.date_prevue + bt.duree_previsionnelle)
                if bt.duree_previsionnelle
                else bt.date_prevue
            )

            data.append(
                {
                    "id": bt.id,
                    "nom": bt.nom,
                    "start": start,
                    "end": end,
                    "equipement": {
                        "id": bt.demande_intervention.equipement.id,
                        "nom": bt.demande_intervention.equipement.designation,
                    }
                    if bt.demande_intervention and bt.demande_intervention.equipement
                    else None,
                    "techniciens": [
                        {
                            "id": user.id,
                            "nom": user.get_full_name() or user.username,
                        }
                        for user in bt.utilisateur_assigne.all()
                    ],
                }
            )
        return Response(data, status=status.HTTP_200_OK)


class TypePlanMaintenanceViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les types de plans de maintenance.

    Liste des endpoints:
    - GET /types-plan-maintenance/ : Liste tous les types
    - POST /types-plan-maintenance/ : Crée un nouveau type
    - GET /types-plan-maintenance/{id}/ : Détail d'un type
    - PUT/PATCH /types-plan-maintenance/{id}/ : Modifie un type
    - DELETE /types-plan-maintenance/{id}/ : Supprime un type
    """

    queryset = TypePlanMaintenance.objects.all()
    serializer_class = TypePlanMaintenanceSerializer


class PlanMaintenanceViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les plans de maintenance.

    Liste des endpoints:
    - GET /plans-maintenance/ : Liste tous les plans
    - POST /plans-maintenance/ : Crée un nouveau plan
    - GET /plans-maintenance/{id}/ : Détail d'un plan
    - PUT/PATCH /plans-maintenance/{id}/ : Modifie un plan
    - DELETE /plans-maintenance/{id}/ : Supprime un plan
    - GET /plans-maintenance/par_equipement/?equipement_id=X : Filtre par équipement
    - GET /plans-maintenance/par_type/?type_id=X : Filtre par type
    - POST /plans-maintenance/{id}/ajouter_consommable/ : Ajoute un consommable
    - POST /plans-maintenance/{id}/retirer_consommable/ : Retire un consommable
    - POST /plans-maintenance/{id}/ajouter_document/ : Ajoute un document
    - POST /plans-maintenance/{id}/retirer_document/ : Retire un document
    """

    queryset = PlanMaintenance.objects.select_related(
        "type_plan_maintenance", "equipement"
    ).prefetch_related("documents", "consommables")
    serializer_class = PlanMaintenanceSerializer

    def get_serializer_class(self):
        """Utilise le serializer détaillé pour retrieve"""
        return PlanMaintenanceSerializer

    @action(detail=False, methods=["post"])
    def forcer_calcul(self, request):
        """
        Force immédiatement le calcul des maintenances préventives, sans
        attendre l'exécution nocturne des tâches planifiées (cron).

        Enchaîne les deux traitements du cron :
        1. Mise à jour des compteurs calendaires à la date du jour.
        2. Vérification des seuils et génération des bons de travail préventifs.
        """
        from tasks.counterCron import update_counter
        from tasks.updateCalendarDates import update_calendar_counters

        try:
            update_calendar_counters()
            bt_crees = update_counter() or 0
            if bt_crees > 0:
                message = f"{bt_crees} bon(s) de travail préventif(s) généré(s)."
            else:
                message = "Calcul effectué : aucun nouveau bon de travail à générer."
            return Response({"message": message, "bt_crees": bt_crees}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Erreur lors du calcul des maintenances préventives : {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def par_equipement(self, request):
        """
        Filtre les plans de maintenance par équipement
        Query param: equipement_id
        """
        equipement_id = request.query_params.get("equipement_id")
        if not equipement_id:
            return Response(
                {"error": "Le paramètre equipement_id est requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plans = self.queryset.filter(equipement_id=equipement_id)
        serializer = self.get_serializer_class()(plans, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Création d'un nouveau plan de maintenance"""
        data = dict(request.data)

        print(data)

        # Extraire les valeurs uniques des listes
        for key, value in data.items():
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        try:
            seuil_data = json.loads(data.get("seuil", "{}"))
            pm_data = seuil_data.get("planMaintenance", {})
        except (json.JSONDecodeError, TypeError):
            return Response(
                {"error": "Format JSON invalide pour le seuil ou le plan de maintenance"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Vérifier que type_id existe et n'est pas null
            type_id = pm_data.get("type_id")
            if not type_id:
                return Response(
                    {"error": "Le type de plan de maintenance est obligatoire"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Vérifier que equipment_id existe
            equipment_id = seuil_data.get("equipmentId")
            if not equipment_id:
                return Response(
                    {"error": "L'équipement est obligatoire"}, status=status.HTTP_400_BAD_REQUEST
                )

            plan = PlanMaintenance.objects.create(
                nom=pm_data.get("nom", ""),
                commentaire=pm_data.get("commentaire", ""),
                necessiteHabilitationElectrique=pm_data.get(
                    "necessiteHabilitationElectrique", False
                ),
                necessitePermisFeu=pm_data.get("necessitePermisFeu", False),
                type_plan_maintenance_id=type_id,
                equipement_id=equipment_id,
            )

            # Créer les consommables associés si fournis
            for consommable in pm_data.get("consommables", []):
                PlanMaintenanceConsommable.objects.create(
                    plan_maintenance=plan,
                    consommable_id=consommable.get("consommable_id"),
                    quantite_necessaire=consommable.get("quantite", 1),
                )

        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création du plan de maintenance: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from equipement.models import Declencher

            # Vérifier que compteur_id existe
            compteur_id = seuil_data.get("compteurId")
            if not compteur_id:
                return Response(
                    {"error": "Le compteur est obligatoire pour le déclenchement"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Declencher.objects.create(
                derniereIntervention=seuil_data.get("derniereIntervention", 0),
                prochaineMaintenance=seuil_data.get("prochaineMaintenance", 0),
                ecartInterventions=seuil_data.get("ecartInterventions", 0),
                estGlissant=seuil_data.get("estGlissant", False),
                compteur_id=compteur_id,
                planMaintenance=plan,
            )

        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création du seuil de déclenchement: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Créer les documents associés si fournis
        uploaded_files = request.FILES.getlist("documents")
        document_metadata_list = pm_data.get("documents", [])

        # Dans la partie création des documents :
        try:
            for index, uploaded_file in enumerate(uploaded_files):
                # Récupérer les métadonnées correspondantes si elles existent
                metadata = None
                if index < len(document_metadata_list):
                    metadata = document_metadata_list[index]

                # Nom du document : depuis les métadonnées ou le nom du fichier
                nom_document = ""
                if metadata and metadata.get("nomDocument"):
                    nom_document = metadata.get("nomDocument")
                else:
                    # Utiliser le nom du fichier sans extension comme nom par défaut
                    nom_document = os.path.splitext(uploaded_file.name)[0]

                # Type de document : depuis les métadonnées ou valeur par défaut
                type_document_id = 1  # Valeur par défaut
                if metadata and metadata.get("typeDocument_id"):
                    type_document_id = metadata.get("typeDocument_id")

                # Créer le Document avec le nom de fichier original
                document = Document.objects.create(
                    nomDocument=nom_document,
                    typeDocument_id=type_document_id,
                    cheminAcces=uploaded_file,  # Django utilise le nom original du fichier
                )

                # Puis créer l'association avec le plan de maintenance
                PlanMaintenanceDocument.objects.create(plan_maintenance=plan, document=document)

        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création des documents: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Sérialiser et retourner la réponse
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Mise à jour d'un plan de maintenance existant"""
        data = dict(request.data)

        print("Données reçues pour update:", data)

        # Extraire les valeurs uniques des listes
        for key, value in data.items():
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        # Parser le JSON des changements
        try:
            changes_json = data.get("changes")
            if changes_json:
                changes = json.loads(changes_json)
                print("Changements détectés:", changes)
            else:
                changes = {}
                print("Aucun changement détecté")
        except json.JSONDecodeError as e:
            print(f"Erreur parsing changes JSON: {e}")
            changes = {}

        # Parser le JSON du seuil si présent
        try:
            seuil_json = data.get("seuil")
            if seuil_json:
                seuil_data = json.loads(seuil_json)
                print("Données seuil:", seuil_data)
            else:
                seuil_data = {}
        except json.JSONDecodeError as e:
            print(f"Erreur parsing seuil JSON: {e}")
            seuil_data = {}

        plan = self.get_object()
        plan = self.get_object()
        has_changes = False  # Pour regrouper toutes les modifications

        # 1. Mettre à jour les champs simples du plan de maintenance
        simple_fields = [
            "nom",
            "commentaire",
            "necessiteHabilitationElectrique",
            "necessitePermisFeu",
            "type_plan_maintenance_id",
        ]

        for field in simple_fields:
            if field in data:
                old_value = getattr(plan, field, None)
                new_value = data[field]
                if old_value != new_value:
                    setattr(plan, field, new_value)
                if old_value != new_value:
                    setattr(plan, field, new_value)
                    has_changes = True

        # 2. Gérer les modifications détectées depuis le frontend
        if changes:
            for field_path, change_data in changes.items():
                # Pour les champs simples du seuil
                if field_path in [
                    "derniereIntervention",
                    "prochaineMaintenance",
                    "ecartInterventions",
                    "estGlissant",
                    "planMaintenanceId",
                ]:
                    # Ces champs concernent le déclenchement, pas le plan
                    print(f"Changement dans le déclenchement: {field_path}")
                    continue

                # Pour les champs du plan de maintenance
                elif field_path.startswith("planMaintenance."):
                    field_name = field_path.replace("planMaintenance.", "")
                    if field_name == "type_id":
                        field_name = "type_plan_maintenance_id"

                    # Les consommables sont traités plus bas dans un bloc dédié.
                    # Ne pas tenter d'assigner directement le M2M.
                    if field_name == "consommables":
                        continue

                    # Vérifier si le champ existe dans le modèle
                    if hasattr(plan, field_name):
                        old_value = getattr(plan, field_name, None)
                        new_value = change_data.get("nouvelle")

                        # Pour les champs booléens, s'assurer du type
                        if field_name in ["necessiteHabilitationElectrique", "necessitePermisFeu"]:
                            new_value = bool(new_value)

                        if old_value != new_value:
                            setattr(plan, field_name, new_value)
                        if old_value != new_value:
                            setattr(plan, field_name, new_value)
                            has_changes = True

        # Sauvegarder les modifications du plan
        # Sauvegarder les modifications du plan
        if has_changes:
            plan.save()

        # 3. Mettre à jour les consommables si nécessaire
        if changes and "planMaintenance.consommables" in changes:
            consommable_change = changes["planMaintenance.consommables"]
            print("Changement des consommables détecté")

            # Récupérer les anciens consommables
            consommable_change.get("ancienne", [])
            new_consommables = consommable_change.get("nouvelle", [])

            # Supprimer les anciennes associations
            plan.consommables.all().delete()

            # Créer les nouvelles associations
            for cons in new_consommables:
                PlanMaintenanceConsommable.objects.create(
                    plan_maintenance=plan,
                    consommable_id=cons.get("consommable_id"),
                    quantite_necessaire=cons.get("quantite", 1),
                )

        # 4. Mettre à jour le déclenchement associé
        try:
            if seuil_data:
                from equipement.models import Declencher

                # Chercher le déclenchement associé à ce plan
                declencher = Declencher.objects.filter(planMaintenance=plan).first()

                if declencher:
                    declencher_has_changes = False

                    # Mettre à jour les champs du déclenchement
                    fields_to_update = [
                        "derniereIntervention",
                        "prochaineMaintenance",
                        "ecartInterventions",
                        "estGlissant",
                    ]

                    for field in fields_to_update:
                        if field in seuil_data:
                            old_value = getattr(declencher, field, None)
                            new_value = seuil_data[field]
                            if old_value != new_value:
                                setattr(declencher, field, new_value)
                            if old_value != new_value:
                                setattr(declencher, field, new_value)
                                declencher_has_changes = True

                    # Sauvegarder les modifications du déclenchement
                    if declencher_has_changes:
                        declencher.save()

                    # Mettre à jour le compteur si changement
                    compteur_id = seuil_data.get("compteurId")
                    if compteur_id and declencher.compteur_id != compteur_id:
                        declencher.compteur_id = compteur_id
                        declencher.save()

        except Exception as e:
            print(f"Erreur lors de la mise à jour du déclenchement: {e}")

        # 5. Mettre à jour les documents si fichiers uploadés
        try:
            uploaded_files = request.FILES.getlist("documents")
            if uploaded_files:
                print(f"{len(uploaded_files)} fichiers uploadés")

                # Récupérer les métadonnées des documents
                documents_metadata = []
                if seuil_data.get("planMaintenance", {}).get("documents"):
                    documents_metadata = seuil_data["planMaintenance"]["documents"]

                for index, uploaded_file in enumerate(uploaded_files):
                    metadata = None
                    if index < len(documents_metadata):
                        metadata = documents_metadata[index]

                    nom_document = metadata.get("nomDocument", "") if metadata else ""
                    type_document_id = metadata.get("typeDocument_id", 1) if metadata else 1

                    if not nom_document:
                        nom_document = os.path.splitext(uploaded_file.name)[0]

                    # Créer le document
                    document = Document.objects.create(
                        nomDocument=nom_document,
                        typeDocument_id=type_document_id,
                        cheminAcces=uploaded_file,
                    )

                    # Créer l'association
                    PlanMaintenanceDocument.objects.create(plan_maintenance=plan, document=document)

        except Exception as e:
            print(f"Erreur lors de la création des documents: {e}")

        serializer = self.get_serializer(plan)
        return Response(serializer.data)


class PlanMaintenanceConsommableViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les associations consommables/plans de maintenance.

    Liste des endpoints:
    - GET /plan-maintenance-consommables/ : Liste toutes les associations
    - POST /plan-maintenance-consommables/ : Crée une nouvelle association
    - GET /plan-maintenance-consommables/{id}/ : Détail d'une association
    - PUT/PATCH /plan-maintenance-consommables/{id}/ : Modifie une association
    - DELETE /plan-maintenance-consommables/{id}/ : Supprime une association
    """

    queryset = PlanMaintenanceConsommable.objects.select_related("plan_maintenance", "consommable")
    serializer_class = PlanMaintenanceConsommableSerializer


class DashboardStatsViewset(viewsets.ViewSet):
    def list(self, request):
        user_id = request.query_params.get("userId")
        user = Utilisateur.objects.filter(pk=user_id).first()
        if not user:
            return Response({"detail": "Utilisateur not found"}, status=status.HTTP_404_NOT_FOUND)

        perms = self.get_dashboard_permissions(user)

        stats = []

        if "dash:stats.full" in perms:
            stats = [
                {
                    "label": "Nombre de DI",
                    "value": DemandeIntervention.objects.filter(
                        ~Q(statut="TRANSFORMEE"), archive=False
                    ).count(),
                },
                {
                    "label": "DI en attente",
                    "value": DemandeIntervention.objects.filter(
                        statut="EN_ATTENTE", archive=False
                    ).count(),
                },
                {
                    "label": "DI acceptées",
                    "value": DemandeIntervention.objects.filter(
                        statut="ACCEPTEE", archive=False
                    ).count(),
                },
                {
                    "label": "Nombre de BT",
                    "value": BonTravail.objects.filter(~Q(statut="CLOTURE"), archive=False).count(),
                },
                {
                    "label": "BT en retard",
                    "value": BonTravail.objects.filter(statut="EN_RETARD", archive=False).count(),
                },
                {
                    "label": "BT en cours",
                    "value": BonTravail.objects.filter(statut="EN_COURS", archive=False).count(),
                },
            ]

        elif "dash:stats.bt" in perms:
            bt = BonTravail.objects.filter(utilisateur_assigne=user)
            stats = [
                {
                    "label": "Vos BT",
                    "value": bt.filter(~Q(statut="CLOTURE"), archive=False).count(),
                },
                {
                    "label": "Vos BT en cours",
                    "value": bt.filter(statut="EN_COURS", archive=False).count(),
                },
                {
                    "label": "Vos BT terminés",
                    "value": bt.filter(statut="TERMINE", archive=False).count(),
                },
            ]

        elif "dash:stats.di" in perms:
            di = DemandeIntervention.objects.filter(utilisateur=user)
            stats = [
                {
                    "label": "Vos DI",
                    "value": DemandeIntervention.objects.filter(utilisateur=user)
                    .filter(~Q(statut="TRANSFORMEE"), archive=False)
                    .count(),
                },
                {
                    "label": "Vos DI en attente",
                    "value": di.filter(statut="EN_ATTENTE", archive=False).count(),
                },
                {
                    "label": "Vos DI acceptées",
                    "value": di.filter(statut="ACCEPTEE", archive=False).count(),
                },
            ]
        else:
            return Response({"detail": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"stats": stats}, status=status.HTTP_200_OK)

    def get_dashboard_permissions(self, user):
        """Récupère les permissions de l'utilisateur pour les stats du dashboard"""
        from utilisateur.models import UtilisateurPermission

        # Si l'utilisateur a des permissions personnalisées, les utiliser
        perms_perso = UtilisateurPermission.objects.filter(
            utilisateur=user, permission__nomPermission__startswith="dash"
        ).values_list("permission__nomPermission", flat=True)

        if perms_perso.exists():
            return list(perms_perso)

        # Sinon, utiliser les permissions du rôle
        return list(
            user.role.permissions.filter(nomPermission__startswith="dash").values_list(
                "nomPermission", flat=True
            )
        )


class MaintenanceCalendarViewSet(viewsets.ViewSet):
    def list(self, request):
        """Récupère tous les déclenchmenets de compteurs calendaires"""
        from equipement.models import Declencher

        declenchements = Declencher.objects.select_related(
            "planMaintenance", "planMaintenance__equipement", "compteur"
        ).filter(compteur__type="CALENDAIRE")
        data = []
        for decl in declenchements:
            plan = decl.planMaintenance
            equipement = plan.equipement if plan else None
            data.append(
                {
                    "id": decl.id,
                    "derniereIntervention": decl.derniereIntervention,
                    "prochaineMaintenance": decl.prochaineMaintenance,
                    "ecartInterventions": decl.ecartInterventions,
                    "estGlissant": decl.estGlissant,
                    "compteur": {
                        "id": decl.compteur_id,
                        "nom": decl.compteur.nomCompteur if decl.compteur else None,
                    }
                    if decl.compteur
                    else None,
                    "planMaintenance": {
                        "id": plan.id,
                        "nom": plan.nom,
                    }
                    if plan
                    else None,
                    "equipement": {
                        "id": equipement.id,
                        "nom": equipement.designation,
                    }
                    if equipement
                    else None,
                }
            )

        return Response(data, status=status.HTTP_200_OK)
