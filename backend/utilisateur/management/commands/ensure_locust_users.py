import os

from django.core.management.base import BaseCommand

from utilisateur.models import Role, Utilisateur

ROLE_CONFIGS = [
    {
        "role_name": "Responsable GMAO",
        "username_env": "LOCUST_RESPONSABLE_USERNAME",
        "default_username": "locust_responsable",
        "first_name": "Locust",
        "last_name": "Responsable",
    },
    {
        "role_name": "Technicien prod",
        "username_env": "LOCUST_TECHNICIEN_USERNAME",
        "default_username": "locust_technicien",
        "first_name": "Locust",
        "last_name": "Technicien",
    },
    {
        "role_name": "Magasinier",
        "username_env": "LOCUST_MAGASINIER_USERNAME",
        "default_username": "locust_magasinier",
        "first_name": "Locust",
        "last_name": "Magasinier",
    },
    {
        "role_name": "Op\u00e9rateur",
        "username_env": "LOCUST_OPERATEUR_USERNAME",
        "default_username": "locust_operateur",
        "first_name": "Locust",
        "last_name": "Operateur",
    },
]


class Command(BaseCommand):
    help = "Create or update dedicated Locust users for the dev environment."

    def handle(self, *args, **options):
        password = os.getenv("LOCUST_PASSWORD", "locust123").strip()
        if not password:
            self.stdout.write(
                self.style.WARNING("LOCUST_PASSWORD is empty; skipping Locust user provisioning.")
            )
            return

        for config in ROLE_CONFIGS:
            username = os.getenv(
                config["username_env"],
                config["default_username"],
            ).strip()
            if not username:
                self.stdout.write(
                    self.style.WARNING(
                        f"{config['username_env']} is empty; skipping {config['role_name']}."
                    )
                )
                continue

            try:
                role = Role.objects.get(nomRole=config["role_name"])
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Role '{config['role_name']}' does not exist; skipping.")
                )
                continue

            email = f"{username}@gimao.local"
            user, created = Utilisateur.objects.get_or_create(
                nomUtilisateur=username,
                defaults={
                    "prenom": config["first_name"],
                    "nomFamille": config["last_name"],
                    "email": email,
                    "actif": True,
                    "role": role,
                },
            )

            changed = created
            if user.prenom != config["first_name"]:
                user.prenom = config["first_name"]
                changed = True
            if user.nomFamille != config["last_name"]:
                user.nomFamille = config["last_name"]
                changed = True
            if user.email != email:
                user.email = email
                changed = True
            if user.role_id != role.id:
                user.role = role
                changed = True
            if not user.actif:
                user.actif = True
                changed = True

            user.set_password(password)
            changed = True

            if changed:
                user.save()

            action = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(f"Locust user {username} ({config['role_name']}) {action}.")
            )
