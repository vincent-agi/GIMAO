from django.core.management.base import BaseCommand

from tasks.updateBtStatus import update_bt_status


class Command(BaseCommand):
    help = "Lance la mise à jour des compteurs (Cron manuel)"

    def handle(self, *args, **options):
        self.stdout.write("Lancement du cron update_bt_status...")
        try:
            update_bt_status()
            self.stdout.write(self.style.SUCCESS("Cron terminé avec succès."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'exécution du cron : {str(e)}"))
