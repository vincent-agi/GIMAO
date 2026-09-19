from django.core.management.base import BaseCommand

from tasks.counterCron import update_counter


class Command(BaseCommand):
    help = "Lance la mise à jour des compteurs (Cron manuel)"

    def handle(self, *args, **options):
        self.stdout.write("Lancement du cron update_counter...")
        try:
            update_counter()
            self.stdout.write(self.style.SUCCESS("Cron terminé avec succès."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'exécution du cron : {str(e)}"))
