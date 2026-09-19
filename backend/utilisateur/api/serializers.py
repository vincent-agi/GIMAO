from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from utilisateur.models import Log, Module, Permission, Role, Utilisateur, UtilisateurPermission

# ==================== MODULE ====================


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Module"""

    class Meta:
        model = Module
        fields = ["id", "code", "nom"]


# ==================== PERMISSION ====================


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Permission"""

    module = ModuleSerializer(read_only=True)

    class Meta:
        model = Permission
        fields = ["id", "nomPermission", "description", "type", "parent_id", "module"]


# ==================== ROLE ====================


class RoleSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Role - inclut les permissions du rôle"""

    permissions = PermissionSerializer(many=True, read_only=True)
    permissions_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        source="permissions",
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = ["id", "nomRole", "estDefaut", "permissions", "permissions_ids"]
        read_only_fields = ["id", "estDefaut"]

    def create(self, validated_data):
        permissions = validated_data.pop("permissions", [])
        role = Role.objects.create(**validated_data)
        if permissions:
            role.permissions.set(permissions)
        return role

    def update(self, instance, validated_data):
        permissions = validated_data.pop("permissions", None)
        instance.nomRole = validated_data.get("nomRole", instance.nomRole)
        # instance.rang = validated_data.get('rang', instance.rang)
        instance.save()
        if permissions is not None:
            instance.permissions.set(permissions)
        return instance


# ==================== UTILISATEUR ====================


class UtilisateurSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Utilisateur"""

    photoProfil = serializers.FileField(required=False, allow_null=True, use_url=False)
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=True
    )
    permissions_names = serializers.SerializerMethodField()
    a_permissions_personnalisees = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "nomUtilisateur",
            "prenom",
            "nomFamille",
            "email",
            "photoProfil",
            "derniereConnexion",
            "dateCreation",
            "actif",
            "role",
            "role_id",
            "permissions_names",
            "a_permissions_personnalisees",
        ]
        read_only_fields = ["derniereConnexion", "dateCreation"]

    def _get_prefetched_permissions_personnalisees(self, obj):
        return getattr(obj, "_prefetched_objects_cache", {}).get("permissions_personnalisees")

    def get_permissions_names(self, obj):
        """
        Retourne les permissions de l'utilisateur.
        Si des permissions personnalisées existent, elles remplacent celles du rôle.
        Sinon, on retourne les permissions du rôle.
        """
        perms_perso = self._get_prefetched_permissions_personnalisees(obj)
        if perms_perso is not None:
            if perms_perso:
                return [up.permission.nomPermission for up in perms_perso]
        else:
            perms_perso = UtilisateurPermission.objects.filter(utilisateur=obj).select_related(
                "permission"
            )
            if perms_perso.exists():
                return [up.permission.nomPermission for up in perms_perso]

        if obj.role:
            return [perm.nomPermission for perm in obj.role.permissions.all()]
        return []

    def get_a_permissions_personnalisees(self, obj):
        """Indique si l'utilisateur a des permissions personnalisées"""
        perms_perso = self._get_prefetched_permissions_personnalisees(obj)
        if perms_perso is not None:
            return bool(perms_perso)
        return obj.permissions_personnalisees.exists()


class UtilisateurCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'utilisateur avec mot de passe"""

    photoProfil = serializers.FileField(required=False, allow_null=True, use_url=False)
    motDePasse = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={"input_type": "password"},
        min_length=8,
    )
    motDePasse_confirmation = serializers.CharField(
        write_only=True, required=False, allow_blank=True, style={"input_type": "password"}
    )
    permissions_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "nomUtilisateur",
            "motDePasse",
            "motDePasse_confirmation",
            "prenom",
            "nomFamille",
            "email",
            "photoProfil",
            "actif",
            "role",
            "permissions_ids",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "nomUtilisateur": {"required": True, "allow_blank": False},
            "prenom": {"required": True, "allow_blank": False},
            "nomFamille": {"required": True, "allow_blank": False},
            "email": {"required": True, "allow_blank": False},
            "actif": {"required": True},
            "role": {"required": True, "allow_null": False},
        }

    def validate(self, data):
        """Vérifie que les mots de passe correspondent"""
        mot_de_passe = data.get("motDePasse")
        confirmation = data.get("motDePasse_confirmation")

        if mot_de_passe in (None, "") and confirmation in (None, ""):
            return data

        if mot_de_passe in (None, "") or confirmation in (None, ""):
            raise serializers.ValidationError(
                {"motDePasse_confirmation": "Confirmation du mot de passe requise"}
            )

        if mot_de_passe != confirmation:
            raise serializers.ValidationError(
                {"motDePasse_confirmation": "Les mots de passe ne correspondent pas"}
            )
        return data

    def create(self, validated_data):
        """Crée un utilisateur avec mot de passe hashé et permissions personnalisées optionnelles"""
        validated_data.pop("motDePasse_confirmation", None)
        permissions = validated_data.pop("permissions_ids", [])

        mot_de_passe = validated_data.get("motDePasse")
        if mot_de_passe in (None, ""):
            validated_data["motDePasse"] = None
        else:
            validated_data["motDePasse"] = make_password(mot_de_passe)

        utilisateur = super().create(validated_data)

        # Si des permissions personnalisées sont fournies, on les associe
        if permissions:
            for perm in permissions:
                UtilisateurPermission.objects.create(utilisateur=utilisateur, permission=perm)

        return utilisateur


class UtilisateurDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé avec logs, rôles et permissions personnalisées"""

    photoProfil = serializers.FileField(required=False, allow_null=True, use_url=False)
    role = RoleSerializer(read_only=True)
    logs_recents = serializers.SerializerMethodField()
    avoirs = serializers.SerializerMethodField()
    permissions_names = serializers.SerializerMethodField()
    a_permissions_personnalisees = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "nomUtilisateur",
            "prenom",
            "nomFamille",
            "email",
            "photoProfil",
            "derniereConnexion",
            "dateCreation",
            "actif",
            "role",
            "logs_recents",
            "avoirs",
            "permissions_names",
            "a_permissions_personnalisees",
        ]

    def get_permissions_names(self, obj):
        perms_perso = obj.permissions_personnalisees.select_related("permission").all()
        if perms_perso.exists():
            return [up.permission.nomPermission for up in perms_perso]
        if obj.role:
            return [perm.nomPermission for perm in obj.role.permissions.all()]
        return []

    def get_a_permissions_personnalisees(self, obj):
        return obj.permissions_personnalisees.exists()

    def get_logs_recents(self, obj):
        """Retourne les 10 derniers logs de l'utilisateur"""
        logs = obj.logs.order_by("-date")[:10]
        return [
            {"id": log.id, "type": log.type, "nomTable": log.nomTable, "date": log.date}
            for log in logs
        ]

    def get_avoirs(self, obj):
        """Retourne les rôles supplémentaires de l'utilisateur"""
        if not hasattr(obj, "avoirs"):
            return []
        try:
            avoirs = obj.avoirs.prefetch_related("roles").all()
        except Exception:
            return []
        return [
            {
                "id": avoir.id,
                "roles": [{"id": r.id, "nomRole": r.nomRole} for r in avoir.roles.all()],
            }
            for avoir in avoirs
        ]


class UtilisateurSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour les relations"""

    class Meta:
        model = Utilisateur
        fields = ["id", "nomUtilisateur", "prenom", "nomFamille", "email", "photoProfil"]


# ==================== AUTHENTIFICATION ====================


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""

    nomUtilisateur = serializers.CharField(required=True)
    motDePasse = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        style={"input_type": "password"},
        write_only=True,
    )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""

    ancien_motDePasse = serializers.CharField(
        required=False, allow_blank=True, style={"input_type": "password"}, write_only=True
    )
    nouveau_motDePasse = serializers.CharField(
        required=True, style={"input_type": "password"}, write_only=True, min_length=8
    )
    nouveau_motDePasse_confirmation = serializers.CharField(
        required=True, style={"input_type": "password"}, write_only=True
    )

    def validate(self, data):
        if data["nouveau_motDePasse"] != data["nouveau_motDePasse_confirmation"]:
            raise serializers.ValidationError(
                {"nouveau_motDePasse_confirmation": "Les mots de passe ne correspondent pas"}
            )
        return data


class DefinirMotDePasseSerializer(serializers.Serializer):
    """Serializer pour définir un mot de passe (première connexion)"""

    nomUtilisateur = serializers.CharField(required=True)
    nouveau_motDePasse = serializers.CharField(
        required=True, style={"input_type": "password"}, write_only=True, min_length=8
    )
    nouveau_motDePasse_confirmation = serializers.CharField(
        required=True, style={"input_type": "password"}, write_only=True
    )

    def validate(self, data):
        if data["nouveau_motDePasse"] != data["nouveau_motDePasse_confirmation"]:
            raise serializers.ValidationError(
                {"nouveau_motDePasse_confirmation": "Les mots de passe ne correspondent pas"}
            )
        return data


# ==================== LOG ====================


class LogSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Log"""

    utilisateur = UtilisateurSimpleSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source="utilisateur",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Log
        fields = [
            "id",
            "type",
            "nomTable",
            "idCible",
            "champsModifies",
            "date",
            "utilisateur",
            "utilisateur_id",
        ]
        read_only_fields = ["date"]
