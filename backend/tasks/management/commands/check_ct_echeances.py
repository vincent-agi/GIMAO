from django.core.management.base import BaseCommand

from tasks.checkCtEcheances import check_ct_echeances


class Command(BaseCommand):
    help = "Envoie une alerte email pour les contrôles techniques à échéance (Cron manuel)"

    def handle(self, *args, **options):
        self.stdout.write("Lancement du job check_ct_echeances...")
        try:
            nombre = check_ct_echeances()
            self.stdout.write(
                self.style.SUCCESS(f"Job terminé : {nombre} notification(s) envoyée(s).")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'exécution du job : {str(e)}"))
