import datetime
from decimal import Decimal

from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict

from .middleware import get_current_user
from .models import Log, Utilisateur


def get_safe_app_user(app_user):
    if not isinstance(app_user, Utilisateur):
        return None

    if not app_user.pk:
        return None

    if not Utilisateur.objects.filter(pk=app_user.pk).exists():
        return None

    return app_user


def resolve_log_actor(candidate_user):
    safe_user = get_safe_app_user(candidate_user)
    if safe_user is not None:
        return safe_user

    if getattr(candidate_user, "is_authenticated", False):
        username = getattr(candidate_user, "username", None)
        if username:
            return Utilisateur.objects.filter(nomUtilisateur=username).first()

    return None


def make_serializable(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    if isinstance(obj, FieldFile):
        return obj.name
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    if hasattr(obj, "pk"):
        return obj.pk

    return obj


def should_ignore_model(sender):
    if sender._meta.model_name in ["log", "session", "contenttype", "migration", "adminlog"]:
        return True

    db_table = getattr(sender._meta, "db_table", "")
    if (
        db_table.startswith("auth")
        or db_table.startswith("django")
        or db_table.startswith("security")
    ):
        return True

    return False


@receiver(pre_save)
def capture_old_state(sender, instance, **kwargs):
    # Ignore specific models to prevent clutter or recursion
    if should_ignore_model(sender):
        return
    if instance.pk:
        try:
            # We fetch the specific fields to avoid overhead, but model_to_dict needs an instance
            old_instance = sender.objects.get(pk=instance.pk)
            # We manually construct dict to handle non-editable fields if needed,
            # but model_to_dict is safer for generic use
            instance._old_state = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if should_ignore_model(sender):
        return

    # Determine action
    action = "création" if created else "modification"

    # Calculate changes
    champs_modifies = {}

    if created:
        for field in instance._meta.fields:
            try:
                val = getattr(instance, field.name)
                # Only log non-empty values for creation to keep log clean?
                # Or everything. Let's log everything that is not None/Empty
                if val not in [None, ""]:
                    champs_modifies[field.name] = {"nouveau": make_serializable(val)}
            except Exception:
                pass
    else:
        # Update
        old_state = getattr(instance, "_old_state", {})
        new_state = model_to_dict(instance)

        # Check for diffs
        # We iterate over new_state because it represents the current fields interesting for the model
        for key, val in new_state.items():
            old_val = old_state.get(key)
            if old_val != val:
                champs_modifies[key] = {
                    "ancien": make_serializable(old_val),
                    "nouveau": make_serializable(val),
                }

    if not champs_modifies and not created:
        return

    if not champs_modifies and not created:
        return

    # Get User from Thread Local (now seamlessly handles token and fallback)
    from .middleware import get_current_user, get_thread_log_group

    app_user = resolve_log_actor(get_current_user())
    log_group_id = get_thread_log_group()

    # Enrich idCible with FKs for association tables
    id_cible = {"id": instance.pk}
    for field in sender._meta.fields:
        if field.is_relation and field.many_to_one and field.concrete:
            try:
                val = getattr(instance, field.attname)
                if val is not None:
                    id_cible[field.name] = make_serializable(
                        val
                    )  # field.name is cleaner than attname (usually field_id)
            except Exception:
                pass

    try:
        if id_cible is None:
            print("WARNING: id_cible is None; user id not send or not found")
        Log.objects.create(
            type=action,
            nomTable=sender._meta.db_table or sender._meta.model_name,
            idCible=id_cible,
            champsModifies=champs_modifies,
            utilisateur=app_user,
            group=log_group_id,
        )
    except Exception as e:
        print(f"Error creating log: {e}")


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if should_ignore_model(sender):
        return

    from .middleware import get_thread_log_group

    log_group_id = get_thread_log_group()

    app_user = resolve_log_actor(get_current_user())

    # Enrich idCible with FKs
    id_cible = {"id": instance.pk}
    for field in sender._meta.fields:
        if field.is_relation and field.many_to_one and field.concrete:
            try:
                val = getattr(instance, field.attname)
                if val is not None:
                    id_cible[field.name] = make_serializable(val)
            except Exception:
                pass

    try:
        Log.objects.create(
            type="suppression",
            nomTable=sender._meta.db_table or sender._meta.model_name,
            idCible=id_cible,
            champsModifies={"deleted": True},
            utilisateur=app_user,
            group=log_group_id,
        )
    except Exception as e:
        print(f"Error creating log: {e}")
