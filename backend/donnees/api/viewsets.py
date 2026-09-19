from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from donnees.api.serializers import (
    AdresseSerializer,
    DocumentSerializer,
    DocumentSimpleSerializer,
    FabricantSerializer,
    FournisseurSerializer,
    LieuDetailSerializer,
    LieuSerializer,
    TypeDocumentSerializer,
)
from donnees.models import Adresse, Document, Fabricant, Fournisseur, Lieu, TypeDocument
from gimao.viewsets import GimaoModelViewSet


class AdresseViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les adresses.
    """

    queryset = Adresse.objects.all()
    serializer_class = AdresseSerializer


class LieuViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les lieux.
    """

    queryset = Lieu.objects.all()
    serializer_class = LieuSerializer

    def get_serializer_class(self):
        """Utilise le serializer détaillé pour retrieve"""
        if self.action == "retrieve":
            return LieuDetailSerializer
        return LieuSerializer

    @action(detail=False, methods=["get"])
    def hierarchy(self, request):
        """
        Retourne une hiérarchie complète : racines + enfants récursifs
        """

        def build_tree(lieu):
            children = Lieu.objects.filter(lieuParent=lieu)
            return {
                "id": lieu.id,
                "nomLieu": lieu.nomLieu,
                "typeLieu": lieu.typeLieu,
                "lienPlan": lieu.lienPlan,
                "lieuParent": lieu.lieuParent_id,
                "children": [build_tree(child) for child in children],
            }

        racines = Lieu.objects.filter(lieuParent__isnull=True)
        data = [build_tree(lieu) for lieu in racines]

        return Response(data)

    @action(detail=False, methods=["get"])
    def racines(self, request):
        """
        Retourne tous les lieux racines (sans parent)
        """
        lieux_racines = Lieu.objects.filter(lieuParent__isnull=True)
        serializer = self.get_serializer(lieux_racines, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def enfants(self, request, pk=None):
        """
        Retourne tous les enfants directs d'un lieu
        """
        lieu = self.get_object()
        enfants = Lieu.objects.filter(lieuParent=lieu)
        serializer = self.get_serializer(enfants, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Création d'un lieu avec ou sans parent
        """
        data = request.data
        nom = data.get("nomLieu")
        parent_id = data.get("lieuParent")
        type_lieu = data.get("typeLieu")

        # Si on a un parent, vérifier qu'il existe
        parent = None
        if parent_id:
            try:
                parent = Lieu.objects.get(id=parent_id)
            except Lieu.DoesNotExist:
                return Response(
                    {"error": "Le lieu parent spécifié n'existe pas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        lieu = Lieu.objects.create(nomLieu=nom, lieuParent=parent, typeLieu=type_lieu)

        return Response(self.get_serializer(lieu).data, status=status.HTTP_201_CREATED)


class TypeDocumentViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les types de documents.
    """

    queryset = TypeDocument.objects.all()
    serializer_class = TypeDocumentSerializer


class DocumentViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les documents.
    """

    queryset = Document.objects.select_related("typeDocument")
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        """Utilise le serializer simple pour list"""
        if self.action == "list":
            return DocumentSimpleSerializer
        return DocumentSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Crée un document via le CRUD.

        Multipart attendu:
        - cheminAcces: fichier
        - typeDocument_id: id du TypeDocument
        - nomDocument (optionnel)

        Réponse: format `DocumentSerializer` (id/titre/type/type_nom/path).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        # Réponse minimale (DB) pour éviter de propager un format enrichi partout.
        # Les écrans qui ont besoin du format historique continuent d'utiliser list/retrieve.
        out = DocumentSimpleSerializer(document, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """
        Met à jour partiellement un document (nom, type et/ou fichier).

        Payload (JSON ou Multipart):
        - nomDocument (optionnel)
        - typeDocument_id (optionnel)
        - cheminAcces (fichier, optionnel) - remplace l'ancien fichier
        """
        instance = self.get_object()

        # Mise à jour du nom si fourni
        if "nomDocument" in request.data:
            instance.nomDocument = request.data["nomDocument"]

        # Mise à jour du type si fourni
        if "typeDocument_id" in request.data:
            type_id = request.data["typeDocument_id"]
            instance.typeDocument_id = type_id

        # Mise à jour du fichier si fourni
        if "cheminAcces" in request.data and request.data["cheminAcces"]:
            # Supprimer l'ancien fichier physique
            if instance.cheminAcces:
                instance.cheminAcces.delete(save=False)
            # Remplacer par le nouveau fichier
            instance.cheminAcces = request.data["cheminAcces"]

        instance.save()

        # Réponse avec le format simple
        out = DocumentSimpleSerializer(instance, context={"request": request})
        return Response(out.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        Supprime un document et son fichier physique.
        Les liaisons avec DI/BT/PM/Consommables sont supprimées en cascade grâce aux FK on_delete=CASCADE
        dans les tables through (DemandeInterventionDocument, BonTravailDocument, etc).
        """
        instance = self.get_object()

        # Tenter de supprimer le fichier physique si il existe
        if instance.cheminAcces:
            try:
                instance.cheminAcces.delete(save=False)
            except Exception as e:
                # En cas d'erreur (fichier manquant, permission, etc), on continue quand même
                print(f"Erreur lors de la suppression du fichier: {e}")

        # Supprimer l'instance (les liaisons M2M seront supprimées en cascade)
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def par_type(self, request):
        """
        Filtre les documents par type
        Query param: type_id
        """
        type_id = request.query_params.get("type_id")
        if not type_id:
            return Response(
                {"error": "Le paramètre type_id est requis"}, status=status.HTTP_400_BAD_REQUEST
            )

        documents = self.queryset.filter(typeDocument_id=type_id)
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)


class FabricantViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les fabricants.
    """

    queryset = Fabricant.objects.select_related("adresse")
    serializer_class = FabricantSerializer

    def get_serializer_class(self):
        """Utilise le serializer simple pour list"""
        return FabricantSerializer

    @action(detail=False, methods=["get"])
    def avec_sav(self, request):
        """
        Retourne les fabricants qui proposent un service après-vente
        """
        fabricants = self.queryset.filter(serviceApresVente=True)
        serializer = self.get_serializer(fabricants, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Création d'un fabricant avec adresse optionnelle
        """
        data = request.data.copy()
        adresse_data = data.pop("adresse", None)

        # Créer l'adresse seulement si au moins un champ est rempli
        adresse = None
        if adresse_data and any(str(v).strip() for v in adresse_data.values() if v):
            adresse_serializer = AdresseSerializer(data=adresse_data)
            adresse_serializer.is_valid(raise_exception=True)
            adresse = adresse_serializer.save()

        fabricant = Fabricant.objects.create(
            nom=data.get("nom"),
            email=data.get("email"),
            numTelephone=data.get("numTelephone"),
            serviceApresVente=data.get("serviceApresVente", False),
            adresse=adresse,
        )

        serializer = self.get_serializer(fabricant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        fabricant = self.get_object()
        data = request.data.copy()

        # Remove user from data if present to avoid issues, though strictly not needed if not used
        data.pop("user", None)

        # Séparer l'adresse si présente
        adresse_data = data.pop("adresse", None)
        if adresse_data and fabricant.adresse:
            for key, val in adresse_data.items():
                if isinstance(val, dict) and "nouvelle" in val:
                    setattr(fabricant.adresse, key, val["nouvelle"])
            fabricant.adresse.save()

        # Mettre à jour les champs simples du fabricant
        for key, val in data.items():
            if isinstance(val, dict) and "nouvelle" in val:
                setattr(fabricant, key, val["nouvelle"])

        fabricant.save()

        serializer = FabricantSerializer(fabricant)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FournisseurViewSet(GimaoModelViewSet):
    """
    ViewSet pour gérer les fournisseurs.
    """

    queryset = Fournisseur.objects.select_related("adresse")
    serializer_class = FournisseurSerializer

    def get_serializer_class(self):
        """Utilise le serializer simple pour list"""
        return FournisseurSerializer

    @action(detail=False, methods=["get"])
    def avec_sav(self, request):
        """
        Retourne les fournisseurs qui proposent un service après-vente
        """
        fournisseurs = self.queryset.filter(serviceApresVente=True)
        serializer = self.get_serializer(fournisseurs, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Création d'un fournisseur avec adresse optionnelle
        """
        data = request.data.copy()
        adresse_data = data.pop("adresse", None)

        # Créer l'adresse seulement si au moins un champ est rempli
        adresse = None
        if adresse_data and any(str(v).strip() for v in adresse_data.values() if v):
            adresse_serializer = AdresseSerializer(data=adresse_data)
            adresse_serializer.is_valid(raise_exception=True)
            adresse = adresse_serializer.save()

        fournisseur = Fournisseur.objects.create(
            nom=data.get("nom"),
            email=data.get("email"),
            numTelephone=data.get("numTelephone"),
            serviceApresVente=data.get("serviceApresVente", False),
            adresse=adresse,
        )

        serializer = self.get_serializer(fournisseur)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Mise à jour d'un fournisseur avec adresse imbriquée
        """
        fournisseur = self.get_object()
        data = request.data.copy()
        data.pop("user", None)

        # Mise à jour de l'adresse si présente
        adresse_data = data.pop("adresse", None)
        if adresse_data and fournisseur.adresse:
            for key, val in adresse_data.items():
                if isinstance(val, dict) and "nouvelle" in val:
                    setattr(fournisseur.adresse, key, val["nouvelle"])
            fournisseur.adresse.save()

        # Mise à jour des champs simples du fournisseur
        for key, val in data.items():
            if isinstance(val, dict) and "nouvelle" in val:
                setattr(fournisseur, key, val["nouvelle"])

        fournisseur.save()

        serializer = FournisseurSerializer(fournisseur)
        return Response(serializer.data, status=status.HTTP_200_OK)
