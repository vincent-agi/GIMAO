from django.urls import include, path
from rest_framework.routers import DefaultRouter

from utilisateur.api.viewsets import (
    LogViewSet,
    ModuleViewSet,
    PermissionViewSet,
    RoleViewSet,
    UtilisateurViewSet,
)

# Créer le router
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"utilisateurs", UtilisateurViewSet, basename="utilisateur")
router.register(r"logs", LogViewSet, basename="log")
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"modules", ModuleViewSet, basename="module")

# URLs
urlpatterns = [
    path("", include(router.urls)),
]
