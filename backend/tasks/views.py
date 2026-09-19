from io import StringIO

from django.core.management import call_command
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class SeedDemoDataView(APIView):
    """
    POST /api/tasks/seed-demo-data/

    Precharge un jeu de donnees de demonstration (equipements, utilisateurs,
    interventions, stocks) dans la base. Reserve au role Responsable GMAO :
    la commande sous-jacente (`seed_tp_data`) supprime les donnees existantes
    avant de recharger le jeu de demo, ce n'est donc pas une action anodine.
    """

    def post(self, request, *args, **kwargs):
        utilisateur = getattr(request, "api_user", None)
        role = getattr(getattr(utilisateur, "role", None), "nomRole", None)

        if role != "Responsable GMAO":
            return Response(
                {"error": "Seul le Responsable GMAO peut precharger les donnees de demonstration."},
                status=status.HTTP_403_FORBIDDEN,
            )

        output = StringIO()
        try:
            call_command("seed_tp_data", stdout=output)
        except Exception as exc:
            return Response(
                {"error": f"Echec du chargement des donnees de demonstration : {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Donnees de demonstration chargees avec succes.",
                "detail": output.getvalue(),
            },
            status=status.HTTP_200_OK,
        )
