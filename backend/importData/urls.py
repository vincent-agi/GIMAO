from django.urls import path

from .views import EquipementImportTemplateView, EquipementImportView

urlpatterns = [
    path(
        "equipements/template/",
        EquipementImportTemplateView.as_view(),
        name="import-equipements-template",
    ),
    path("equipements/", EquipementImportView.as_view(), name="import-equipements"),
]
