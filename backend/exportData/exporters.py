from django.db import models

from donnees.models import Fabricant, Fournisseur, Lieu
from equipement.models import Compteur, Declencher, Equipement, ModeleEquipement, StatutEquipement
from exportData.formatters import generateCsvResponse, generateXlsxResponse
from maintenance.models import BonTravail, BonTravailConsommable, DemandeIntervention
from stock.models import Consommable, Magasin, PorterSur, Stocker
from utilisateur.models import Log, Utilisateur

exportRegistry = {}


def registerExporter(nom):
    """
    Decorator to register an exporter strategy into the exportRegistry.
    """

    def wrapper(cls):
        exportRegistry[nom] = cls
        return cls

    return wrapper


class BaseExportStrategy:
    """
    Abstract base class for all export strategies.
    Requires `model` to be defined in subclasses.
    """

    model = None

    def __init__(self, request_params):
        """
        :param request_params: Typically request.GET dictionary containing parameters like:
            - exportType: string
            - includeArchived: 'yes', 'no', 'both'
            - columns: list of strings (comma separated in HTTP)
            - fileType: 'csv', 'xlsx'
            - equipementId: ID for filtering
            - magasinId: ID for filtering
            - utilisateurId: ID for filtering
            - consoId: ID for filtering
        """
        self.params = request_params

    def get_queryset(self):
        """
        Fetches the initial queryset and applies the `includeArchived` filter conditionally.
        Then calls `apply_filters` which can be overridden by subclasses.
        """
        if not self.model:
            raise NotImplementedError("Subclasses must define a 'model'.")

        qs = self.model.objects.all()

        # Check if model has an `archive` field safely
        has_archive = any(field.name == "archive" for field in self.model._meta.fields)

        if has_archive:
            include_archived = self.params.get("includeArchived", "no")
            if include_archived == "no":
                qs = qs.filter(archive=False)
            elif include_archived == "yes":
                qs = qs.filter(archive=True)
            # 'both' means no filter

        qs = self.apply_filters(qs)
        qs = self.apply_date_filters(qs)
        return qs

    def apply_filters(self, qs):
        """
        Hook for subclasses to override and apply specific filters (like equipementId).
        """
        return qs

    def apply_date_filters(self, qs):
        """
        Hook for subclasses to override and apply specific date filters (startDate, endDate).
        """
        return qs

    def get_columns(self):
        """
        Extracts columns from the parameters.
        Expects a comma-separated string: 'id,nom,etat'
        """
        columns_str = self.params.get("columns", "")
        if columns_str:
            return [col.strip() for col in columns_str.split(",") if col.strip()]
        return None

    def _get_field_metadata(self):
        """
        Builds a mapping {attname: label}, a set of boolean field attnames,
        and a mapping {attname: fk_name} for ForeignKey fields.
        """
        column_labels = {}
        boolean_fields = set()
        fk_fields = {}
        for field in self.model._meta.fields:
            column_labels[field.attname] = str(field.verbose_name).capitalize()
            if isinstance(field, models.BooleanField):
                boolean_fields.add(field.attname)
            elif isinstance(field, models.ForeignKey):
                fk_fields[field.attname] = field.name
        return column_labels, boolean_fields, fk_fields

    def _format_data(self, data, boolean_fields):
        """
        Converts boolean values (True/False) to 'Oui'/'Non' in the data rows.
        """
        for row in data:
            for field_name in boolean_fields:
                if field_name in row:
                    val = row[field_name]
                    if val is True:
                        row[field_name] = "Oui"
                    elif val is False:
                        row[field_name] = "Non"
        return data

    def _process_row(self, row, obj):
        """Hook for subclasses to mutate a row dictionary right after extraction"""
        return row

    def export(self):
        """
        Executes the export strategy:
        1. Fetch queryset
        2. Filter by columns if requested
        3. Convert booleans to Oui/Non
        4. Format into the requested fileType with readable headers
        """
        qs = self.get_queryset()
        columns = self.get_columns()
        column_labels, boolean_fields, fk_fields = self._get_field_metadata()

        if not columns:
            # Use all field attnames as columns to guarantee consistent ordering
            columns = [field.attname for field in self.model._meta.fields]

        select_related_fields = [fk_fields[col] for col in columns if col in fk_fields]
        if select_related_fields:
            qs = qs.select_related(*select_related_fields)

        data = []
        for obj in qs:
            row = {}
            for col in columns:
                if col in fk_fields:
                    fk_obj = getattr(obj, fk_fields[col], None)
                    row[col] = str(fk_obj) if fk_obj is not None else ""
                else:
                    row[col] = getattr(obj, col, None)

            row = self._process_row(row, obj)
            data.append(row)

        # Convert booleans True/False → Oui/Non
        data = self._format_data(data, boolean_fields)

        file_type = self.params.get("fileType", "csv").lower()
        export_type = self.params.get("exportType", "export")

        if file_type == "xlsx":
            return generateXlsxResponse(
                data, filename=export_type, columns=columns, column_labels=column_labels
            )
        else:
            return generateCsvResponse(
                data, filename=export_type, columns=columns, column_labels=column_labels
            )


# 1. Equipement
@registerExporter("equipement")
class EquipementStrategy(BaseExportStrategy):
    model = Equipement


# 2. Statut Equipement
@registerExporter("statut_equipement")
class StatutEquipementStrategy(BaseExportStrategy):
    model = StatutEquipement

    def apply_filters(self, qs):
        equipement_id = self.params.get("equipementId")
        if equipement_id:
            qs = qs.filter(equipement_id=equipement_id)
        return qs

    def apply_date_filters(self, qs):
        start_date = self.params.get("startDate")
        end_date = self.params.get("endDate")
        if start_date or end_date:
            if start_date and len(start_date) == 10:
                start_date += " 00:00:00"
            if end_date and len(end_date) == 10:
                end_date += " 23:59:59"

            if start_date and end_date:
                date_filter = models.Q(dateChangement__range=[start_date, end_date])
            elif start_date:
                date_filter = models.Q(dateChangement__gte=start_date)
            else:
                date_filter = models.Q(dateChangement__lte=end_date)

            equipements_in_range_ids = list(
                qs.filter(date_filter).values_list("equipement_id", flat=True)
            )

            latest_statut_data = (
                StatutEquipement.objects.exclude(equipement_id__in=equipements_in_range_ids)
                .values("equipement_id")
                .annotate(max_id=models.Max("id"))
            )

            latest_statut_ids = [item["max_id"] for item in latest_statut_data if item["max_id"]]

            qs = qs.filter(date_filter | models.Q(id__in=latest_statut_ids))
        return qs


# 3. BonTravail (bt)
@registerExporter("bt")
class BonTravailStrategy(BaseExportStrategy):
    model = BonTravail

    def apply_filters(self, qs):
        equipement_id = self.params.get("equipementId")
        if equipement_id:
            qs = qs.filter(demande_intervention__equipement_id=equipement_id)
        return qs

    def apply_date_filters(self, qs):
        start_date = self.params.get("startDate")
        end_date = self.params.get("endDate")
        if start_date or end_date:
            if start_date and len(start_date) == 10:
                start_date += " 00:00:00"
            if end_date and len(end_date) == 10:
                end_date += " 23:59:59"

            if start_date and end_date:
                qs = qs.filter(
                    demande_intervention__date_changementStatut__range=[start_date, end_date]
                )
            elif start_date:
                qs = qs.filter(demande_intervention__date_changementStatut__gte=start_date)
            else:
                qs = qs.filter(demande_intervention__date_changementStatut__lte=end_date)
        return qs


# 4. DemandeIntervention (di)
@registerExporter("di")
class DemandeInterventionStrategy(BaseExportStrategy):
    model = DemandeIntervention

    def apply_filters(self, qs):
        equipement_id = self.params.get("equipementId")
        if equipement_id:
            qs = qs.filter(equipement_id=equipement_id)
        return qs

    def apply_date_filters(self, qs):
        start_date = self.params.get("startDate")
        end_date = self.params.get("endDate")
        if start_date or end_date:
            if start_date and len(start_date) == 10:
                start_date += " 00:00:00"
            if end_date and len(end_date) == 10:
                end_date += " 23:59:59"

            if start_date and end_date:
                qs = qs.filter(date_creation__range=[start_date, end_date])
            elif start_date:
                qs = qs.filter(date_creation__gte=start_date)
            else:
                qs = qs.filter(date_creation__lte=end_date)
        return qs


# 5. Consommable (conso)
@registerExporter("conso")
class ConsommableStrategy(BaseExportStrategy):
    model = Consommable


# 6. Historique Achat Consommable (PorterSur)
@registerExporter("historique_achat_conso")
class AchatConsommableStrategy(BaseExportStrategy):
    model = PorterSur

    def apply_filters(self, qs):
        conso_id = self.params.get("consoId")
        if conso_id:
            qs = qs.filter(consommable_id=conso_id)
        return qs

    def apply_date_filters(self, qs):
        start_date = self.params.get("startDate")
        end_date = self.params.get("endDate")
        if start_date or end_date:
            if start_date and len(start_date) == 10:
                start_date += " 00:00:00"
            if end_date and len(end_date) == 10:
                end_date += " 23:59:59"

            if start_date and end_date:
                qs = qs.filter(date_reference_prix__range=[start_date, end_date])
            elif start_date:
                qs = qs.filter(date_reference_prix__gte=start_date)
            else:
                qs = qs.filter(date_reference_prix__lte=end_date)
        return qs


# 7. Stock (Stocker)
@registerExporter("stock")
class StockStrategy(BaseExportStrategy):
    model = Stocker

    def apply_filters(self, qs):
        magasin_id = self.params.get("magasinId")
        if magasin_id:
            qs = qs.filter(magasin_id=magasin_id)
        return qs


# 8. Magasins
@registerExporter("magasins")
class MagasinStrategy(BaseExportStrategy):
    model = Magasin


# 9. Historique Sortie Magasin (BonTravailConsommable)
@registerExporter("historique_sortie_magasin")
class SortieMagasinStrategy(BaseExportStrategy):
    model = BonTravailConsommable

    def apply_filters(self, qs):
        magasin_id = self.params.get("magasinId")
        if magasin_id:
            qs = qs.filter(magasin_reserve_id=magasin_id)
        return qs

    def apply_date_filters(self, qs):
        start_date = self.params.get("startDate")
        end_date = self.params.get("endDate")
        if start_date or end_date:
            if start_date and len(start_date) == 10:
                start_date += " 00:00:00"
            if end_date and len(end_date) == 10:
                end_date += " 23:59:59"

            if start_date and end_date:
                qs = qs.filter(date_confirme__range=[start_date, end_date])
            elif start_date:
                qs = qs.filter(date_confirme__gte=start_date)
            else:
                qs = qs.filter(date_confirme__lte=end_date)
        return qs


# 10. Logs
@registerExporter("logs")
class LogStrategy(BaseExportStrategy):
    model = Log

    def apply_filters(self, qs):
        utilisateur_id = self.params.get("utilisateurId")
        if utilisateur_id:
            qs = qs.filter(utilisateur_id=utilisateur_id)
        return qs

    def apply_date_filters(self, qs):
        start_date = self.params.get("startDate")
        end_date = self.params.get("endDate")
        if start_date or end_date:
            if start_date and len(start_date) == 10:
                start_date += " 00:00:00"
            if end_date and len(end_date) == 10:
                end_date += " 23:59:59"

            if start_date and end_date:
                qs = qs.filter(date__range=[start_date, end_date])
            elif start_date:
                qs = qs.filter(date__gte=start_date)
            else:
                qs = qs.filter(date__lte=end_date)
        return qs


# 11. Fournisseur
@registerExporter("fournisseur")
class FournisseurStrategy(BaseExportStrategy):
    model = Fournisseur


# 12. Fabricant
@registerExporter("fabricant")
class FabricantStrategy(BaseExportStrategy):
    model = Fabricant


# 13. Modele Equipement
@registerExporter("modele_equipement")
class ModeleEquipementStrategy(BaseExportStrategy):
    model = ModeleEquipement


# 14. Lieu
@registerExporter("lieu")
class LieuStrategy(BaseExportStrategy):
    model = Lieu


# 15. Compteur (uniquement numériques)
@registerExporter("compteur")
class CompteurNumeriqueStrategy(BaseExportStrategy):
    model = Compteur

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.exclude(type="Calendaire")
        return qs

    def apply_filters(self, qs):
        equipement_id = self.params.get("equipementId")
        if equipement_id:
            qs = qs.filter(equipement_id=equipement_id)
        return qs


# 16. Seuils de compteurs numériques
@registerExporter("seuils_compteur")
class SeuilCompteurStrategy(BaseExportStrategy):
    model = Declencher

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.exclude(compteur__type="Calendaire")
        return qs

    def apply_filters(self, qs):
        equipement_id = self.params.get("equipementId")
        if equipement_id:
            qs = qs.filter(compteur__equipement_id=equipement_id)
        return qs


# 17. Périodicités (seuils de compteurs calendaires)
@registerExporter("periodicites")
class PeriodiciteStrategy(BaseExportStrategy):
    model = Declencher

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(compteur__type="Calendaire")
        return qs

    def apply_filters(self, qs):
        equipement_id = self.params.get("equipementId")
        if equipement_id:
            qs = qs.filter(compteur__equipement_id=equipement_id)
        return qs

    def apply_date_filters(self, qs):
        start_date = self.params.get("startDate")
        end_date = self.params.get("endDate")
        if start_date or end_date:
            from datetime import datetime

            start_ord = None
            end_ord = None
            try:
                if start_date:
                    start_ord = datetime.strptime(start_date[:10], "%Y-%m-%d").date().toordinal()
                if end_date:
                    end_ord = datetime.strptime(end_date[:10], "%Y-%m-%d").date().toordinal()
            except ValueError:
                pass

            if start_ord and end_ord:
                qs = qs.filter(prochaineMaintenance__range=[start_ord, end_ord])
            elif start_ord:
                qs = qs.filter(prochaineMaintenance__gte=start_ord)
            elif end_ord:
                qs = qs.filter(prochaineMaintenance__lte=end_ord)
        return qs

    def _get_field_metadata(self):
        column_labels, boolean_fields, fk_fields = super()._get_field_metadata()
        if "ecartInterventions" in column_labels:
            column_labels["ecartInterventions"] += " (Jours)"
        return column_labels, boolean_fields, fk_fields

    def _process_row(self, row, obj):
        from datetime import date

        # Récupère les ordinaux bruts AVANT conversion en date
        ord_derniere = row.get("derniereIntervention")
        ord_prochaine = row.get("prochaineMaintenance")

        for field in ["derniereIntervention", "prochaineMaintenance"]:
            if field in row and row[field] is not None:
                try:
                    row[field] = date.fromordinal(int(row[field]))
                except Exception:
                    pass

        # Calcul de l'écart en jours via les ordinaux (insensible au DST)
        if "ecartInterventions" in row:
            try:
                ecart_jours = int(ord_prochaine) - int(ord_derniere)
                row["ecartInterventions"] = ecart_jours
            except Exception:
                row["ecartInterventions"] = ""
        return row


# 17. Utilisateurs
@registerExporter("users")
class UtilisateurStrategy(BaseExportStrategy):
    model = Utilisateur
