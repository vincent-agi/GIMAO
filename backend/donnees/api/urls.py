from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import (
    AdresseViewSet,
    DocumentViewSet,
    FabricantViewSet,
    FournisseurViewSet,
    LieuViewSet,
    TypeDocumentViewSet,
)

# Créer le router
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r"adresses", AdresseViewSet, basename="adresse")
router.register(r"lieux", LieuViewSet, basename="lieu")
router.register(r"types-documents", TypeDocumentViewSet, basename="type-document")
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"fabricants", FabricantViewSet, basename="fabricant")
router.register(r"fournisseurs", FournisseurViewSet, basename="fournisseur")

# URLs
urlpatterns = [
    path("", include(router.urls)),
]
