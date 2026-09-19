from django.apps import AppConfig


class EquipementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "equipement"

    def ready(self):
        import re

        from django.apps import apps

        for model in apps.get_models():
            # Exclude third-party / built-in apps if we don't want to mess up their verbose names,
            # or apply globally if the app label isn't 'admin', 'auth', 'contenttypes', 'sessions'
            if model._meta.app_label in ["admin", "auth", "contenttypes", "sessions", "authtoken"]:
                continue

            for field in model._meta.fields:
                default_verbose_name = field.name.replace("_", " ")
                # If verbose_name wasn't explicitly provided, it matches default_verbose_name
                if str(field.verbose_name) == default_verbose_name:
                    spaced_name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", field.name)
                    spaced_name = spaced_name.replace("_", " ").capitalize()
                    field.verbose_name = spaced_name
