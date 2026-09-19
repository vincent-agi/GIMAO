from django.core.management.base import BaseCommand

from tasks.create_initial_data import create_initial_data


class Command(BaseCommand):
    help = "Lance la création des données initiales (roles, types fixes)"

    def handle(self, *args, **options):
        self.stdout.write("Lancement de la création des données initiales...")
        try:
            create_initial_data()
            self.stdout.write(
                self.style.SUCCESS("Création des données initiales terminée avec succès.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Erreur lors de la création des données initiales : {str(e)}")
            )

        self.stdout.write("------------------------------------------")
