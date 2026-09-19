from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from exportData.exporters import exportRegistry


class ExportView(APIView):
    """
    API View to handle generalized data exports.
    Expects GET parameters:
    - exportType: the registered name of the exporter (e.g. 'equipement', 'bon_travail')
    - fileType: 'csv' or 'xlsx' (default: 'csv')
    - includeArchived: 'yes', 'no', 'both' (default: 'no')
    - columns: comma-separated list of column names (optional)
    """

    def get(self, request, *args, **kwargs):
        export_type = request.GET.get("exportType")

        if not export_type:
            return Response(
                {"error": "Le paramètre 'exportType' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exporter_class = exportRegistry.get(export_type)
        if not exporter_class:
            return Response(
                {
                    "error": f"L'exportType '{export_type}' n'est pas reconnu. Types disponibles: {list(exportRegistry.keys())}"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            # Instantiate the Strategy with the request parameters
            exporter_instance = exporter_class(request.GET)

            qs = exporter_instance.get_queryset()
            if not qs.exists():
                return Response(
                    {"error": "Pas de données pour ces paramètres"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Execute export, returns HttpResponse (CSV or XLSX file)
            return exporter_instance.export()
        except Exception as e:
            return Response(
                {"error": f"Une erreur s'est produite lors de l'export: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportFieldsView(APIView):
    """
    API View to retrieve the available fields (columns) for a given exportType.
    Expects GET parameter 'exportType'.
    """

    def get(self, request, *args, **kwargs):
        export_type = request.GET.get("exportType")

        if not export_type:
            return Response(
                {"error": "Le paramètre 'exportType' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exporter_class = exportRegistry.get(export_type)
        if not exporter_class:
            return Response(
                {"error": f"L'exportType '{export_type}' n'est pas reconnu."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            model = exporter_class.model
            fields = [
                {
                    "value": field.attname,  # Real DB column name (e.g. 'lieu_id' for FK, 'numSerie' for regular)
                    "label": str(field.verbose_name).capitalize(),
                }
                for field in model._meta.fields
            ]
            return Response({"fields": fields}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Erreur de récupération des champs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
