from django.db import models
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response


class ArchivableMixin(models.Model):
    """
    Mixin générique pour rendre un modèle archivable.
    Ajoute automatiquement un champ 'archive' (BooleanField) en BDD.
    """

    archive = models.BooleanField(default=False, help_text="Indique si l'élément est archivé")

    class Meta:
        abstract = True


class ArchivableViewSetMixin:
    """
    Mixin générique pour les ViewSets de modèles archivables.
    - Filtre les éléments archivés sur l'action 'list'
    - Ajoute une action 'set_archive' pour archiver/désarchiver un élément
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        # Sur l'action list, exclure les éléments archivés
        if self.action == "list":
            queryset = queryset.filter(archive=False)
        return queryset

    @action(detail=True, methods=["patch"], url_path="set-archive")
    def set_archive(self, request, pk=None):
        """Archiver ou désarchiver un élément."""
        instance = self.get_object()
        archive_value = request.data.get("archive")

        if archive_value is None:
            return Response(
                {"error": "Le champ 'archive' est requis."}, status=status.HTTP_400_BAD_REQUEST
            )

        instance.archive = bool(archive_value)
        instance.save(update_fields=["archive"])

        return Response({"id": instance.pk, "archive": instance.archive}, status=status.HTTP_200_OK)
