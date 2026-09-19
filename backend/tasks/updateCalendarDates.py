"""
Script pour mettre à jour les compteurs calendaires avec la date du jour.
Les dates calendaires sont stockées sous forme de nombre de jours depuis 1/1/1.
"""

import datetime

from equipement.models import Compteur


def update_calendar_counters():
    """
    Met à jour tous les compteurs de type 'Calendaire' avec la date du jour
    au même format de stockage (nombre de jours depuis 1/1/1).
    """
    # Récupérer tous les compteurs calendaires
    compteurs_calendaires = Compteur.objects.filter(type="Calendaire", equipement__archive=False)

    if not compteurs_calendaires.exists():
        print("Aucun compteur calendaire trouvé.")
        return

    # Calculer le nombre de jours depuis 1/1/1 jusqu'à aujourd'hui
    base_date = datetime.datetime(1, 1, 1)
    aujourd_hui = datetime.datetime.now()
    jours_ecoules = (aujourd_hui - base_date).days

    print(f"Date de base: {base_date}")
    print(f"Aujourd'hui: {aujourd_hui}")
    print(f"Nombre de jours écoulés: {jours_ecoules}")
    print(f"Nombre de compteurs à mettre à jour: {compteurs_calendaires.count()}")
    print("-" * 60)

    # Mettre à jour chaque compteur
    compteurs_updates = []
    for compteur in compteurs_calendaires:
        ancien_val = compteur.valeurCourante
        compteur.valeurCourante = jours_ecoules
        compteurs_updates.append(compteur)

        print(
            f"Compteur {compteur.id} ({compteur.nomCompteur}) - {compteur.equipement.designation}"
        )
        print(f"  Ancienne valeur: {ancien_val}")
        print(f"  Nouvelle valeur: {jours_ecoules}")

    # Sauvegarder tous les compteurs
    Compteur.objects.bulk_update(compteurs_updates, ["valeurCourante"], batch_size=100)

    print("-" * 60)
    print(f"✓ {len(compteurs_updates)} compteur(s) calendaire(s) mis à jour avec succès!")
    print("-" * 60)


if __name__ == "__main__":
    update_calendar_counters()
