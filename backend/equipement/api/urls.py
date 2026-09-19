from django.urls import include, path
from rest_framework.routers import DefaultRouter

from equipement.api.views import EquipementFormDataView
from equipement.api.viewsets import (
    CompteurViewSet,
    ConstituerViewSet,
    DeclenchementViewSet,
    EquipementAffichageViewSet,
    EquipementViewSet,
    FamilleEquipementViewSet,
    ModeleEquipementViewSet,
    StatutEquipementViewSet,
    VehiculeViewSet,
)

router = DefaultRouter()
router.register(r"equipements", EquipementViewSet, basename="equipement")
router.register(r"statut-equipements", StatutEquipementViewSet, basename="statut-equipement")
router.register(r"constituer", ConstituerViewSet, basename="constituer")
router.register(r"modele-equipements", ModeleEquipementViewSet, basename="modele-equipement")
router.register(r"compteurs", CompteurViewSet, basename="compteur")
router.register(r"famille-equipements", FamilleEquipementViewSet, basename="famille-equipement")
router.register(r"declenchements", DeclenchementViewSet, basename="declenchements")
router.register(r"vehicules", VehiculeViewSet, basename="vehicule")

urlpatterns = [
    path(
        "equipements/form-data/",
        EquipementFormDataView.as_view(),
        name="equipement-form-data",
    ),
    path(
        "equipement/<str:id>/affichage/",
        EquipementAffichageViewSet.as_view({"get": "retrieve"}),
        name="equipement-affichage",
    ),
    path("", include(router.urls)),
]
