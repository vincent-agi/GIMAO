import pytest

from donnees.models import Fabricant, Fournisseur, Lieu
from equipement.models import Equipement, FamilleEquipement, ModeleEquipement
from tests.factories import (
    EquipementFactory,
    FabricantFactory,
    FamilleEquipementFactory,
    FournisseurFactory,
    LieuFactory,
    ModeleEquipementFactory,
)


@pytest.mark.django_db
class TestEquipementModels:
    def test_lieu_update(self):
        lieu = LieuFactory(nomLieu="Atelier 1")
        lieu.nomLieu = "Atelier 2"
        lieu.save()
        assert Lieu.objects.get(id=lieu.id).nomLieu == "Atelier 2"

    def test_fabricant_creation(self):
        fab = FabricantFactory(nom="Acme Corp")
        assert Fabricant.objects.filter(nom="Acme Corp").exists()
        # string cast usually uses self.nom or similar
        assert "Acme Corp" in str(fab)

    def test_fournisseur_update(self):
        fourn = FournisseurFactory(nom="Fournisseur A")
        fourn.nom = "Fournisseur B"
        fourn.save()
        assert Fournisseur.objects.get(id=fourn.id).nom == "Fournisseur B"

    def test_famille_equipement_delete(self):
        fam = FamilleEquipementFactory(nom="Famille 1")
        fam_id = fam.id
        fam.delete()
        assert not FamilleEquipement.objects.filter(id=fam_id).exists()

    def test_modele_equipement_relations(self):
        fab = FabricantFactory(nom="Fab Test")
        mod = ModeleEquipementFactory(nom="Modele X", fabricant=fab)
        assert mod.fabricant.nom == "Fab Test"

    def test_equipement_str(self):
        eq = EquipementFactory(designation="Eq1")
        assert "Eq1" in str(eq)

    def test_equipement_famille_relation(self):
        fam = FamilleEquipementFactory(nom="Famille Test")
        eq = EquipementFactory(famille=fam)
        assert eq.famille.nom == "Famille Test"

    def test_equipement_creation_multiple(self):
        EquipementFactory.create_batch(3)
        assert Equipement.objects.count() >= 3
