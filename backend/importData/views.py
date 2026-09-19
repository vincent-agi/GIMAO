import openpyxl
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from importData.importers import EquipementImporter
from importData.template import generate_equipement_template
from utilisateur.models import Utilisateur


class EquipementImportTemplateView(APIView):
    """
    GET /api/import/equipements/template/

    Retourne le classeur Excel modèle à remplir pour l'import en masse
    d'équipements (et de leurs données de référence).
    """

    def get(self, request, *args, **kwargs):
        return generate_equipement_template()


class EquipementImportView(APIView):
    """
    POST /api/import/equipements/ (multipart, champ 'file')

    Importe un classeur Excel rempli à partir du modèle fourni par
    EquipementImportTemplateView. Retourne un résumé (créés / existants /
    erreurs) par onglet traité.
    """

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error": "Aucun fichier reçu. Le champ 'file' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workbook = openpyxl.load_workbook(uploaded_file, data_only=True)
        except Exception:
            return Response(
                {"error": "Le fichier fourni n'est pas un classeur Excel (.xlsx) valide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        utilisateur = None
        utilisateur_id = request.data.get("utilisateur_id")
        if utilisateur_id:
            utilisateur = Utilisateur.objects.filter(id=utilisateur_id).first()
        if not utilisateur:
            utilisateur = Utilisateur.objects.first()

        importer = EquipementImporter(workbook, utilisateur=utilisateur)
        results = importer.run()

        return Response(
            {"resultats": [r.as_dict() for r in results]},
            status=status.HTTP_200_OK,
        )
