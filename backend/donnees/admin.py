from django.contrib import admin

from .models import Adresse, Document, Fabricant, Fournisseur, Lieu, TypeDocument

# ==================== MIXINS (DRY) ====================


class ContactAdminMixin:
    """
    Mixin réutilisable pour les modèles ayant les mêmes champs de contact
    (Fabricant, Fournisseur).
    """

    list_display = ("nom", "email", "numTelephone", "serviceApresVente")
    list_filter = ("serviceApresVente",)
    search_fields = ("nom", "email")
    ordering = ("nom",)


# ==================== DONNÉES DE RÉFÉRENCE ====================


@admin.register(Lieu)
class LieuAdmin(admin.ModelAdmin):
    list_display = ("id", "nomLieu", "typeLieu", "lieuParent")
    list_filter = ("typeLieu",)
    search_fields = ("nomLieu",)
    ordering = ("nomLieu",)


@admin.register(TypeDocument)
class TypeDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "nomTypeDocument")
    search_fields = ("nomTypeDocument",)
    ordering = ("nomTypeDocument",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "nomDocument", "typeDocument")
    list_filter = ("typeDocument",)
    search_fields = ("nomDocument",)
    ordering = ("nomDocument",)


@admin.register(Fabricant)
class FabricantAdmin(ContactAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Fournisseur)
class FournisseurAdmin(ContactAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Adresse)
class AdresseAdmin(admin.ModelAdmin):
    list_display = ("id", "numero", "rue", "ville", "code_postal", "pays")
    search_fields = ("rue", "ville", "code_postal", "pays")
    ordering = ("pays", "ville", "rue")
