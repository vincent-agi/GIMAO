from django.core.management.base import BaseCommand

from tasks.updateCalendarDates import update_calendar_counters


class Command(BaseCommand):
    help = "Lance la mise à jour des dates de compteurs (Cron manuel)"

    def handle(self, *args, **options):
        self.stdout.write("Lancement du cron update_calendar_counters...")
        try:
            update_calendar_counters()
            self.stdout.write(self.style.SUCCESS("Cron terminé avec succès."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'exécution du cron : {str(e)}"))
