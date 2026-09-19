# gimao/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from gimao.views import home_view
from maintenance.api.viewsets import BonTravailViewSet
from tasks.views import SeedDemoDataView

# ---- Personnalisation de l'interface d'administration ----
admin.site.site_header = "GIMAO — Administration"
admin.site.site_title = "GIMAO Admin"
admin.site.index_title = "Tableau de bord d'administration"

schema_view = get_schema_view(
    openapi.Info(
        title="GIMAO API",
        default_version="v1",
        description="Documentation de l'API GIMAO - Gestion Informatisée de Maintenance Assistée par Ordinateur",
        contact=openapi.Contact(email="contact@gimao.local"),
        license=openapi.License(name="GNU Affero General Public License v3"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),
    # Swagger / API Documentation
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # API endpoints
    path(
        "api/bons-travail/<int:pk>/update_consommable_distribution/",
        BonTravailViewSet.as_view({"patch": "update_consommable_distribution"}),
        name="bon-travail-update-consommable-distribution-direct",
    ),
    path(
        "api/bons-travail/<int:pk>/cancel_mise_de_cote/",
        BonTravailViewSet.as_view({"patch": "cancel_mise_de_cote"}),
        name="bon-travail-cancel-mise-de-cote-direct",
    ),
    path(
        "api/bons-travail/<int:pk>/set_recupere/",
        BonTravailViewSet.as_view({"patch": "set_recupere"}),
        name="bon-travail-set-recupere-direct",
    ),
    path("api/", include("equipement.api.urls")),
    path("api/", include("maintenance.api.urls")),
    path("api/", include("utilisateur.api.urls")),
    path("api/", include("donnees.api.urls")),
    path("api/", include("stock.api.urls")),
    path("api/export/", include("exportData.urls")),
    path("api/import/", include("importData.urls")),
    path("api/tasks/seed-demo-data/", SeedDemoDataView.as_view(), name="seed-demo-data"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
