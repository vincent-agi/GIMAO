import json
import datetime
from django.db.models import Prefetch
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db import transaction
from django.shortcuts import get_object_or_404

# Models
from donnees.models import Document
from equipement.models import *
from utilisateur.models import Log

# Serializers
from equipement.api.serializers import (
    EquipementSerializer,
    StatutEquipementSerializer,
    ConstituerSerializer,
    ModeleEquipementSerializer,
    CompteurSerializer,
    FamilleEquipementSerializer,
    EquipementAffichageSerializer,
    EquipementCreateSerializer,
    DeclenchementSerializer
)

from maintenance.models import (
    PlanMaintenance,
    PlanMaintenanceConsommable,
    PlanMaintenanceDocument,
    DemandeInterventionDocument,
    BonTravailDocument,
)
from gimao.viewsets import GimaoModelViewSet
from gimao.mixins import ArchivableViewSetMixin
from gimao.pagination import LargePagination
from equipement import services


class EquipementListPagination(LargePagination):
    pass


class EquipementViewSet(ArchivableViewSetMixin, GimaoModelViewSet):
    """
    CRUD sur les équipements physiques avec filtrage avancé.

    Filtres disponibles (query params) :
        lieu_ids   — liste d'IDs séparés par des virgules (ex: lieu_ids=1,2,3).
        search     — recherche sur reference, designation, numSerie, lieu, modele.

    Actions custom :
        PATCH /api/equipements/{id}/set-archive/      — archive l'équipement et clôture tous ses BT/DI associés.
        GET   /api/equipements/{id}/historique_statuts/ — historique chronologique des changements de statut.
        GET   /api/equipements/{id}/kpi/              — indicateurs MTBF, MTTR, nombre de pannes.
        POST  /api/equipements/{id}/add_document/     — attache un fichier à l'équipement.

    La logique métier (création/mise à jour imbriquée, archivage en cascade,
    calcul de KPI) est déléguée au module ``equipement.services`` : ce
    ViewSet ne fait que router, sérialiser et traduire les erreurs métier en
    réponses HTTP (cf. ADR-001, TUS-003).
    """
    queryset = Equipement.objects.select_related("lieu", "modele").prefetch_related(
        Prefetch(
            "documents",
            queryset=Document.objects.only("id"),
        ),
        Prefetch(
            "statuts",
            queryset=StatutEquipement.objects.only(
                "id",
                "statut",
                "dateChangement",
                "equipement_id",
            ).order_by("-dateChangement"),
            to_attr="prefetched_statuts",
        )
    )
    pagination_class = EquipementListPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["reference", "designation", "numSerie", "lieu__nomLieu", "modele__nom"]
    ordering_fields = ["id", "reference", "designation", "dateCreation"]
    ordering = ["designation", "id"]

    def get_queryset(self):
        queryset = super().get_queryset()

        lieu_ids = self.request.query_params.get("lieu_ids")
        if lieu_ids:
            ids = [int(value) for value in lieu_ids.split(",") if value.strip().isdigit()]
            if ids:
                queryset = queryset.filter(lieu_id__in=ids)

        modele_ids = self.request.query_params.get("modele_ids")
        if modele_ids:
            ids = [int(value) for value in modele_ids.split(",") if value.strip().isdigit()]
            if ids:
                queryset = queryset.filter(modele_id__in=ids)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return EquipementCreateSerializer
        return EquipementSerializer

    @action(detail=True, methods=['patch'], url_path='set-archive')
    @transaction.atomic
    def set_archive(self, request, pk=None):
        """Archive l'équipement puis clôture en cascade ses DI/BT liés."""
        response = super().set_archive(request, pk=pk)

        if response.status_code == status.HTTP_200_OK:
            instance = self.get_object()
            if instance.archive:
                services.archive_equipement_cascade(instance)

        return response

    @action(detail=True, methods=['get'], url_path='historique_statuts')
    def historique_statuts(self, request, pk=None):
        """Retourne l'historique chronologique des statuts d'un équipement."""
        return Response(services.get_historique_statuts(self.get_object()))

    @action(detail=True, methods=['get'])
    def kpi(self, request, pk=None):
        """Retourne le nombre de pannes, le MTBF et le MTTR de l'équipement."""
        return Response(services.compute_equipement_kpi(self.get_object()))

    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """Attache un document uploadé directement à l'équipement."""
        try:
            document = services.add_document_to_equipement(
                self.get_object(),
                request.FILES.get('file'),
                request.data.get('nomDocument', ''),
                request.data.get('typeDocument_id'),
            )
        except services.DocumentRequisManquant as exc:
            return Response({'error': exc.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'id': document.id, 'nomDocument': document.nomDocument},
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _normalize_create_payload(raw_data: dict) -> dict:
        """Normalise un payload FormData de création (listes à un élément, JSON imbriqué)."""
        data = dict(raw_data)

        for key, value in list(data.items()):
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        if "lieu" in data:
            lieu_value = data["lieu"]
            if isinstance(lieu_value, str):
                try:
                    data["lieu"] = json.loads(lieu_value)["id"]
                except (TypeError, ValueError, KeyError):
                    pass
            elif isinstance(lieu_value, dict):
                data["lieu"] = lieu_value["id"]

        for field in ["consommables", "compteurs", "plansMaintenance"]:
            if field in data and isinstance(data[field], str):
                data[field] = json.loads(data[field])

        return data

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Crée un équipement avec ses consommables, compteurs et plans de maintenance imbriqués."""
        data = self._normalize_create_payload(request.data)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        try:
            equipement = services.create_equipement(data, request.FILES, getattr(request, "user", None))
        except services.UtilisateurCreateurIntrouvable as exc:
            return Response({"error": exc.message}, status=status.HTTP_401_UNAUTHORIZED)
        except services.DocumentRequisManquant as exc:
            return Response({"error": exc.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(EquipementSerializer(equipement).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Met à jour un équipement à partir d'un diff de changements (``changes`` en FormData)."""
        equipement = self.get_object()

        data = dict(request.data)
        for key, value in list(data.items()):
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        changes_data = data.get("changes")
        if not changes_data:
            return Response(
                {"error": "Aucune donnée de changement fournie"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            changes = json.loads(changes_data)
        except json.JSONDecodeError:
            return Response(
                {"error": "Format JSON invalide pour les changements"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        equipement = services.update_equipement(equipement, changes, request.FILES)

        return Response(EquipementSerializer(equipement).data, status=status.HTTP_200_OK)


class StatutEquipementViewSet(GimaoModelViewSet):
    """Enregistrement des changements de statut d'un équipement. Utilisé en lecture pour construire la timeline."""
    queryset = StatutEquipement.objects.all()
    serializer_class = StatutEquipementSerializer


class ConstituerViewSet(GimaoModelViewSet):
    """Liaison équipement–consommable : déclare qu'un consommable est utilisé par un équipement."""
    queryset = Constituer.objects.all()
    serializer_class = ConstituerSerializer


class ModeleEquipementViewSet(GimaoModelViewSet):
    """CRUD sur les modèles d'équipements. La création gère l'association avec le fabricant."""
    queryset = ModeleEquipement.objects.all()
    serializer_class = ModeleEquipementSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Création d'un nouveau modèle d'équipement"""
        data = request.data
        print(f"Data reçue pour création modèle : {data}")
        
        # Extraire le nom et le fabricant_id
        nom = data.get('nom')
        fabricant_id = data.get('fabricant')
        
        if not nom:
            return Response(
                {"error": "Le nom du modèle est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not fabricant_id:
            return Response(
                {"error": "Le fabricant est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer le modèle
        try:
            modele = ModeleEquipement.objects.create(
                nom=nom,
                fabricant_id=fabricant_id
            )
            
            # Retourner le modèle créé avec le serializer
            serializer = self.get_serializer(modele)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            print(f"Erreur lors de la création du modèle : {str(e)}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Mise à jour d'un modèle d'équipement - gère aussi les consommables associés"""
        modele = self.get_object()
        data = request.data
        print(f"Data reçue : {data}")
        
        changes = data
        print(f"Changes : {changes}")
        
        
        # Mise à jour des champs du modèle
        if 'nom' in changes:
            field_data = changes['nom']
            nouvelle_valeur = field_data.get('nouvelle')
            ancienne_valeur = field_data.get('ancienne')
                        
            if nouvelle_valeur is not None:
                old_value = modele.nom
                
                if str(old_value) != str(nouvelle_valeur):
                    modele.nom = nouvelle_valeur

        
        if 'fabricant' in changes:
            field_data = changes['fabricant']
            nouvelle_valeur = field_data.get('nouvelle')
            ancienne_valeur = field_data.get('ancienne')
                        
            if nouvelle_valeur is not None:
                old_value = modele.fabricant_id
                
                if old_value != nouvelle_valeur:
                    modele.fabricant_id = nouvelle_valeur
        
        # Vérifier s'il y a eu des changements (excluant 'user')
        has_changes = any(key in changes for key in ['nom', 'fabricant'])
        
        if has_changes:
            modele.save()

        return Response(
            ModeleEquipementSerializer(modele).data,
            status=status.HTTP_200_OK
        )


class CompteurViewSet(GimaoModelViewSet):
    """
    CRUD sur les compteurs de maintenance d'un équipement.

    La création accepte un payload JSON imbriqué (``compteur`` + ``plan_maintenance`` + ``seuil``
    optionnel) pour créer en une seule requête le compteur, son plan de maintenance et son seuil
    de déclenchement. Les compteurs de type ``Calendaire`` stockent leurs valeurs comme numéros
    de jour ordinaux Python (``date.toordinal()``).
    """
    queryset = Compteur.objects.all()
    serializer_class = CompteurSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Création d'un nouveau compteur avec plan de maintenance optionnel"""
        try:
            # Parser les données JSON du compteur
            compteur_data = json.loads(request.data.get('compteur', '{}'))

            print(f"Données reçues pour création compteur : {compteur_data}")
            
            # Vérifier que l'équipement est fourni
            equipement_id = compteur_data.get('equipement')
            if not equipement_id:
                return Response(
                    {"error": "L'ID de l'équipement est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer l'équipement
            try:
                equipement = Equipement.objects.get(id=equipement_id)
            except Equipement.DoesNotExist:
                return Response(
                    {"error": "Équipement introuvable"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Traiter le cas ou on a une date
            if compteur_data.get('type') == 'Calendaire' and 'valeurCourante' in compteur_data:
                valeurCourante = self.formatFromDateToDays(compteur_data.get('valeurCourante'))
            else:
                # sinon convertir en nombre
                try:
                    valeurCourante = float(compteur_data.get('valeurCourante', 0))
                except (ValueError, TypeError):
                    valeurCourante = 0


            
            # Créer le compteur
            compteur = Compteur.objects.create(
                equipement=equipement,
                nomCompteur=compteur_data.get('nom', ''),
                valeurCourante=valeurCourante,
                unite=compteur_data.get('unite', 'heures'),
                estPrincipal=compteur_data.get('estPrincipal', False),
                type=compteur_data.get('type', 'Numérique')
            )

            
            # Retourner le compteur créé
            serializer = CompteurSerializer(compteur)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except json.JSONDecodeError:
            return Response(
                {"error": "Format JSON invalide"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def formatFromDateToDays(self, date_str):
        try:
            date_value = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            base_date = datetime.datetime(1, 1, 1)  # Date de référence
            delta = date_value - base_date
            print(f"Conversion de la date {date_str} en jours: {delta.days}")
            return delta.days
        except Exception:
            print(f"Erreur de conversion de la date {date_str}, retour 0")
            return 0

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """ Mise à jour d'un compteur """      
        changes = request.data
        compteur = self.get_object()
        print(f"Data reçue pour mise à jour du compteur {compteur.id} : {changes}")    

        if len(changes.keys()) == 0:
            return Response(
                {"message": "Aucune modification détectée."},
                status=status.HTTP_200_OK
            )

        # Mettre à jour les champs du compteur
        field_mapping = {
            'nomCompteur': 'nomCompteur',
            'valeurCourante': 'valeurCourante',
            'unite': 'unite',
            'estPrincipal': 'estPrincipal',
            'type': 'type'
        }

        for field, model_field in field_mapping.items():
            if field in changes:
                field_data = changes[field]
                nouvelle_valeur = field_data.get('nouveau')
                ancienne_valeur = field_data.get('ancien')
                
                if nouvelle_valeur is not None:
                    old_value = getattr(compteur, model_field)
                    if field == 'valeurCourante' and compteur.type == 'Calendaire':
                            # Convertir la date en jours
                            nouvelle_valeur = self.formatFromDateToDays(nouvelle_valeur)
                    
                    if str(old_value) != str(nouvelle_valeur):                       

                        setattr(compteur, model_field, nouvelle_valeur)
                        

        compteur.save()
        return Response(
            CompteurSerializer(compteur).data,
            status=status.HTTP_200_OK
        )
    


class FamilleEquipementViewSet(GimaoModelViewSet):
    """CRUD sur les familles d'équipements. Supporte une hiérarchie parent–enfant via ``familleParente``."""
    queryset = FamilleEquipement.objects.all()
    serializer_class = FamilleEquipementSerializer


class EquipementAffichageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour l'affichage détaillé des équipements"""
    serializer_class = EquipementAffichageSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Equipement.objects.select_related(
            'lieu', 'modele__fabricant', 'famille'
        ).prefetch_related(
            'statuts',
            'compteurs',
            'documents'
        )




class DeclenchementViewSet(GimaoModelViewSet):
    """ ViewSet pour les seuils (declenchement): création/modification """

    queryset = Declencher.objects.all()
    serializer_class = DeclenchementSerializer


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """ Creation d'un Seuil avec PM & compteur """
        # Récupération et normalisation des données
        data = dict(request.data)

        print(f"Données reçues pour création déclenchement : {data}")

        # Extraire les valeurs uniques des listes (compatibilité FormData)
        for key, value in list(data.items()):
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]

        # Parser les objets JSON s'ils sont envoyés en tant que chaînes
        plan_data = data.get('planMaintenance') or {}
        if isinstance(plan_data, str):
            try:
                plan_data = json.loads(plan_data)
            except json.JSONDecodeError:
                plan_data = {}

        seuil = data.get('seuil') or {}
        if isinstance(seuil, str):
            try:
                seuil = json.loads(seuil)
            except json.JSONDecodeError:
                seuil = {}

        # Récupérer le compteur existant ou créer un compteur minimal si on fournit un equipmentId
        compteur_id = data.get('compteur') or data.get('compteurId')
        equipment_id = data.get('equipmentId') or data.get('equipement') or data.get('equipmentId')

        compteur = None
        if compteur_id:
            try:
                compteur = Compteur.objects.get(id=compteur_id)
            except Compteur.DoesNotExist:
                return Response({'error': 'Compteur introuvable'}, status=status.HTTP_404_NOT_FOUND)
        else:
            if not equipment_id:
                return Response({'error': 'Il faut fournir "compteur" ou "equipmentId"'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                equipment = Equipement.objects.get(id=equipment_id)
            except Equipement.DoesNotExist:
                return Response({'error': 'Équipement introuvable'}, status=status.HTTP_404_NOT_FOUND)

            # Créer un compteur par défaut lié à l'équipement
            compteur = Compteur.objects.create(
                equipement=equipment,
                nomCompteur=plan_data.get('nom', f"Compteur pour {equipment.id}"),
                valeurCourante=0,
                unite=plan_data.get('unite', 'heures'),
                estPrincipal=False,
                type=plan_data.get('type', 'Général')
            )

        pm_id = plan_data.get('id') or plan_data.get('planMaintenanceId')
        plan = None
        if pm_id:
            try:
                plan = PlanMaintenance.objects.get(id=pm_id)
            except PlanMaintenance.DoesNotExist:
                return Response({'error': 'Plan de maintenance introuvable'}, status=status.HTTP_404_NOT_FOUND)
        
        else :
            # Créer le plan de maintenance
            plan = PlanMaintenance.objects.create(
                equipement=compteur.equipement,
                nom=plan_data.get('nom') or f"Plan {compteur.nomCompteur}",
                type_plan_maintenance_id=plan_data.get('type_id') or plan_data.get('type'),
                commentaire=plan_data.get('description') or plan_data.get('commentaire', ''),
                necessiteHabilitationElectrique=bool(plan_data.get('necessiteHabilitationElectrique', False)),
                necessitePermisFeu=bool(plan_data.get('necessitePermisFeu', False))
            )

        # Créer le déclencheur (seuil)
        derniere = seuil.get('derniereIntervention') or seuil.get('derniereintervention') or 0
        prochaine = seuil.get('prochaineMaintenance') or seuil.get('prochainemaintenance') or 0
        ecart = seuil.get('ecartInterventions') or seuil.get('intervalle') or 0
        est_glissant = seuil.get('estGlissant', False)

        # Détection calendaire : par type OU par nature des données (ISO string)
        is_calendaire = (
            compteur.type == 'Calendaire' or
            compteur.unite == 'date' or
            isinstance(derniere, str) and '-' in str(derniere)
        )

        if is_calendaire:
            # Convertir en ordinal
            derniere = self.date_to_days(derniere) if isinstance(derniere, str) else int(derniere or 0)
            prochaine = self.date_to_days(prochaine) if isinstance(prochaine, str) else int(prochaine or 0)
            # Garder ecart tel quel (timestamp MS)
            ecart = int(ecart) if isinstance(ecart, str) else int(ecart or 0)
        else:
            try:
                prochaine = float(derniere or 0) + float(ecart or 0)
            except (TypeError, ValueError):
                prochaine = float(ecart or 0)

        anticipation = data.get('anticipationJours')
        anticipation_val = int(anticipation) if anticipation else None

        declencher = Declencher.objects.create(
            compteur=compteur,
            planMaintenance=plan,
            derniereIntervention=derniere,
            ecartInterventions=ecart,
            prochaineMaintenance=prochaine,
            estGlissant=bool(est_glissant),
            anticipationJours=anticipation_val
        )

        # Consommables pour le plan
        for conso in plan_data.get('consommables', []) or []:
            if isinstance(conso, dict):
                consommable_id = conso.get('consommable_id') or conso.get('consommable')
                quantite = conso.get('quantite_necessaire') or conso.get('quantite') or 1
            else:
                consommable_id = conso
                quantite = 1

            if consommable_id:
                PlanMaintenanceConsommable.objects.create(
                    plan_maintenance=plan,
                    consommable_id=consommable_id,
                    quantite_necessaire=quantite
                )

        # Documents pour le plan
        documents = plan_data.get('documents', []) or []
        for doc_index, doc_data in enumerate(documents):
            # Récupérer le fichier uploadé depuis FormData
            file_key = f'document_{doc_index}'
            uploaded_file = request.FILES.get(file_key)

            if uploaded_file:
                # Créer le document
                document = Document.objects.create(
                    nomDocument=doc_data.get('titre', uploaded_file.name),
                    cheminAcces=uploaded_file,
                    typeDocument_id=doc_data.get('type')
                )

                # Lier le document au plan
                PlanMaintenanceDocument.objects.create(
                    plan_maintenance=plan,
                    document=document
                )

        serializer = DeclenchementSerializer(declencher)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def date_to_days(self, date_str: str) -> int:
        """
        Convertit 'YYYY-MM-DD' → nombre de jours depuis 0001-01-01
        """
        try:
            date_value = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            base_date = datetime.datetime(1, 1, 1)  # Date de référence
            delta = date_value - base_date
            print(f"Conversion de la date {date_str} en jours: {delta.days}")
            return delta.days
        except Exception:
            print(f"Erreur de conversion de la date {date_str}, retour 0")
            return 0
        
        

    @transaction.atomic
    def partial_update(self, request, pk=None):
        declenchement = get_object_or_404(Declencher, pk=pk)
        utilisateur = request.user if request.user.is_authenticated else None

        seuil_diff = json.loads(request.data.get('seuil_diff', '{}'))
        pm_diff = json.loads(request.data.get('planMaintenance_diff', '{}'))

        logs = []

        # ============================
        # 1. MISE À JOUR DU SEUIL
        # ============================
        if seuil_diff:
            def to_float(value, default=0.0):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return default

            def to_int(value, default=0):
                try:
                    return int(float(value))
                except (TypeError, ValueError):
                    return default

            for champ, valeurs in seuil_diff.items():
                if champ in ['derniereIntervention', 'prochaineMaintenance', 'ecartInterventions']:
                    # Si c'est un champ de date, convertir en jours
                    if champ in ['derniereIntervention', 'prochaineMaintenance'] and declenchement.compteur.type == 'Calendaire':
                        nouvelle_valeur = self.date_to_days(valeurs.get('nouveau'))
                        setattr(declenchement, champ, nouvelle_valeur)
                    else:
                        nouvelle_valeur = valeurs.get('nouveau')
                        if champ == 'derniereIntervention':
                            setattr(declenchement, champ, to_int(nouvelle_valeur))
                        else:
                            setattr(declenchement, champ, to_float(nouvelle_valeur))

                elif hasattr(declenchement, champ):
                    setattr(declenchement, champ, valeurs.get('nouveau'))

            declenchement.save()

            logs.append(Log(
                type="modification",
                nomTable="gimao_declencher",
                idCible={"id": declenchement.id},
                champsModifies=seuil_diff,
                utilisateur=utilisateur
            ))

        # ============================
        # 2. MISE À JOUR PLAN MAINTENANCE
        # ============================
        plan = declenchement.planMaintenance

        if plan and pm_diff:
            for champ, valeurs in pm_diff.items():

                # Champs simples
                if champ in [
                    "nom",
                    "commentaire",
                    "necessiteHabilitationElectrique",
                    "necessitePermisFeu"
                ]:
                    setattr(plan, champ, valeurs.get("nouveau"))

                # Type de PM
                elif champ == "type_id":
                    plan.type_plan_maintenance_id = valeurs.get("nouveau")

                # Consommables
                elif champ == "consommables":
                    PlanMaintenanceConsommable.objects.filter(
                        plan_maintenance=plan
                    ).delete()

                    for c in valeurs.get("nouveau", []):
                        PlanMaintenanceConsommable.objects.create(
                            plan_maintenance=plan,
                            consommable_id=c.get("consommable_id"),
                            quantite_necessaire=c.get("quantite_necessaire", 1)
                        )

                # Documents
                elif champ == "documents":
                    old_doc_ids = list(
                        plan.planmaintenancedocument_set.values_list(
                            "document_id", flat=True
                        )
                    )

                    PlanMaintenanceDocument.objects.filter(plan_maintenance=plan).delete()

                    kept_doc_ids = set()
                    for index, doc in enumerate(valeurs.get("nouveau", [])):
                        file_key = f"document_{index}"
                        uploaded_file = request.FILES.get(file_key)

                        # Front attendu: {nom, type_id, document_id}. Fallback minimal: {titre, type} / {id}
                        titre_value = (doc.get("nom") or doc.get("titre") or "")
                        type_document_id = (doc.get("type_id") or doc.get("type") or None)
                        existing_document_id = (doc.get("document_id") or doc.get("id"))

                        if isinstance(type_document_id, str) and type_document_id.isdigit():
                            type_document_id = int(type_document_id)

                        # 1) Réutiliser / mettre à jour un document existant
                        if existing_document_id:
                            try:
                                document = Document.objects.get(id=existing_document_id)
                            except Document.DoesNotExist:
                                return Response(
                                    {"error": f"Document introuvable (id={existing_document_id})"},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )

                            if uploaded_file is not None:
                                if type_document_id in (None, ""):
                                    return Response(
                                        {
                                            "error": f"Type manquant pour le document #{index + 1}"
                                        },
                                        status=status.HTTP_400_BAD_REQUEST,
                                    )

                                # Remplacement du fichier: supprimer l'ancien fichier physique
                                try:
                                    if document.cheminAcces:
                                        document.cheminAcces.delete(save=False)
                                except Exception:
                                    # Ne pas casser une mise à jour si le fichier est déjà manquant
                                    pass

                                document.nomDocument = titre_value or uploaded_file.name
                                document.typeDocument_id = type_document_id
                                document.cheminAcces = uploaded_file
                                document.save()

                            kept_doc_ids.add(document.id)
                            PlanMaintenanceDocument.objects.create(
                                plan_maintenance=plan,
                                document=document,
                            )
                            continue

                        # 2) Création d'un nouveau document (nécessite un fichier)
                        if uploaded_file is None:
                            # Pas d'id + pas de fichier => rien à créer / lier
                            continue

                        if type_document_id in (None, ""):
                            return Response(
                                {"error": f"Type manquant pour le document #{index + 1}"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                        document = Document.objects.create(
                            nomDocument=titre_value or uploaded_file.name,
                            typeDocument_id=type_document_id,
                            cheminAcces=uploaded_file,
                        )
                        kept_doc_ids.add(document.id)
                        PlanMaintenanceDocument.objects.create(
                            plan_maintenance=plan,
                            document=document,
                        )

                    # Nettoyage: supprimer les documents retirés si non référencés ailleurs
                    removed_doc_ids = set(old_doc_ids) - kept_doc_ids
                    for removed_id in removed_doc_ids:
                        # Si le doc est encore lié ailleurs, ne pas le supprimer
                        still_used = (
                            PlanMaintenanceDocument.objects.filter(document_id=removed_id).exists()
                            or DemandeInterventionDocument.objects.filter(
                                document_id=removed_id
                            ).exists()
                            or BonTravailDocument.objects.filter(document_id=removed_id).exists()
                            or DocumentEquipement.objects.filter(document_id=removed_id).exists()
                        )
                        if still_used:
                            continue

                        try:
                            doc_obj = Document.objects.get(id=removed_id)
                        except Document.DoesNotExist:
                            continue

                        try:
                            if doc_obj.cheminAcces:
                                doc_obj.cheminAcces.delete(save=False)
                        except Exception:
                            pass
                        doc_obj.delete()

            plan.save()

            logs.append(Log(
                type="modification",
                nomTable="gimao_plan_maintenance",
                idCible={"id": plan.id},
                champsModifies=pm_diff,
                utilisateur=utilisateur
            ))

        # ============================
        # 3. LOGS
        # ============================
        if logs:
            Log.objects.bulk_create(logs)

        return Response(
            {"detail": "Modifications appliquées avec succès"},
            status=status.HTTP_200_OK
        )
