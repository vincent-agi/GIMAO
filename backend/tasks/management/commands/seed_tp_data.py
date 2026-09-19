"""
Commande de seed pour les séances TP.
Vide toute la base (sauf migrations et données de référence) puis la remplit
avec un jeu de données : utilisateurs, équipements, DI, BT, stocks…

Usage :
    python manage.py seed_tp_data
    python manage.py seed_tp_data --flush   # force la suppression avant seed

Docker :
    docker compose -f docker-compose.prod.yml exec backend python manage.py seed_tp_data
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Réinitialise la base de données avec des données de démonstration pour le TP"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Supprime toutes les données existantes avant le seed (défaut : oui)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== SEED DONNÉES TP ==="))
        self.stdout.write("Suppression des données existantes...")
        self._flush_data()
        self.stdout.write("Création des données de référence (rôles, permissions)...")
        self._init_reference_data()
        # create_initial_data() crée un "responsable" sans mot de passe — on le supprime
        # pour que _create_users() puisse créer le compte complet
        from utilisateur.models import Utilisateur

        Utilisateur.objects.filter(nomUtilisateur="responsable").delete()

        self.stdout.write("Création des données TP...")
        with transaction.atomic():
            self._seed()
        self.stdout.write(self.style.SUCCESS("=== SEED TERMINÉ AVEC SUCCÈS ==="))
        self._print_summary()

    # ------------------------------------------------------------------
    # 1. FLUSH
    # ------------------------------------------------------------------
    def _flush_data(self):
        from donnees.models import Adresse, Document, Fabricant, Fournisseur, Lieu
        from equipement.models import (
            Compteur,
            Constituer,
            Declencher,
            DocumentEquipement,
            Equipement,
            FamilleEquipement,
            ModeleEquipement,
            StatutEquipement,
        )
        from maintenance.models import (
            BonTravail,
            BonTravailConsommable,
            BonTravailDocument,
            DemandeIntervention,
            DemandeInterventionDocument,
            PlanMaintenance,
            PlanMaintenanceConsommable,
            PlanMaintenanceDocument,
        )
        from security.models import ApiToken
        from stock.models import Consommable, EstCompatible, Magasin, PorterSur, Stocker
        from utilisateur.models import Log, Utilisateur, UtilisateurPermission

        models_to_flush = [
            ApiToken,
            Log,
            BonTravailConsommable,
            BonTravailDocument,
            DemandeInterventionDocument,
            PlanMaintenanceConsommable,
            PlanMaintenanceDocument,
            BonTravail,
            DemandeIntervention,
            PlanMaintenance,
            Constituer,
            DocumentEquipement,
            Declencher,
            StatutEquipement,
            Compteur,
            Equipement,
            ModeleEquipement,
            FamilleEquipement,
            EstCompatible,
            Stocker,
            PorterSur,
            Consommable,
            Magasin,
            Document,
            Fabricant,
            Fournisseur,
            Lieu,
            UtilisateurPermission,
            Utilisateur,
        ]
        for model in models_to_flush:
            count = model.objects.count()
            if count:
                model.objects.all().delete()
                self.stdout.write(f"  Supprimé {count} {model.__name__}")

        # Supprimer les adresses orphelines après coup
        Adresse.objects.all().delete()

    # ------------------------------------------------------------------
    # 2. DONNÉES DE RÉFÉRENCE (rôles, permissions, types)
    # ------------------------------------------------------------------
    def _init_reference_data(self):
        from tasks.create_initial_data import create_initial_data

        create_initial_data()

        # Créer le rôle "Technicien maintenance" avec les mêmes permissions que "Technicien"
        from tasks import perms_data
        from utilisateur.models import Permission, Role, RolePermission

        tech_maint, created = Role.objects.get_or_create(nomRole="Technicien maintenance")
        if created:
            for perm_name in perms_data.perms_map.get("Technicien prod", []):
                try:
                    perm = Permission.objects.get(nomPermission=perm_name)
                    RolePermission.objects.get_or_create(role=tech_maint, permission=perm)
                except Permission.DoesNotExist:
                    pass
            self.stdout.write("  Rôle 'Technicien maintenance' créé")

    # ------------------------------------------------------------------
    # 3. SEED PRINCIPAL
    # ------------------------------------------------------------------
    def _seed(self):
        self._create_users()
        self._create_lieux()
        self._create_fabricants_fournisseurs()
        self._create_familles_modeles()
        self._create_equipements()
        self._create_consommables_magasins()
        self._create_di_bt()

    # ------------------------------------------------------------------
    # UTILISATEURS
    # ------------------------------------------------------------------
    def _create_users(self):
        from utilisateur.models import Role, Utilisateur

        role_resp = Role.objects.get(nomRole="Responsable GMAO")
        role_tech = Role.objects.get(nomRole="Technicien prod")
        role_tm = Role.objects.get(nomRole="Technicien maintenance")
        role_op = Role.objects.get(nomRole="Opérateur prod")
        role_mag = Role.objects.get(nomRole="Magasinier")

        users_data = [
            # (nomUtilisateur, prenom, nomFamille, email, role, password)
            (
                "responsable.gmao",
                "Responsable",
                "GMAO",
                "responsable.gmao@gimao.fr",
                role_resp,
                "Responsable1!",
            ),
            ("t.martin", "Thomas", "Martin", "t.martin@gimao.fr", role_tech, "Technicien1!"),
            ("a.bernard", "Alice", "Bernard", "a.bernard@gimao.fr", role_tech, "Technicien1!"),
            ("l.moreau", "Lucas", "Moreau", "l.moreau@gimao.fr", role_tm, "Technicien1!"),
            ("c.camille", "Camille", "camille", "c.camille@gimao.fr", role_tm, "Technicien1!"),
            ("o.durand", "Olivier", "Durand", "o.durand@gimao.fr", role_op, "Operateur1!"),
            ("s.leroy", "Sophie", "Leroy", "s.leroy@gimao.fr", role_op, "Operateur1!"),
            ("mag.simon", "Pierre", "Simon", "p.simon@gimao.fr", role_mag, "Magasinier1!"),
        ]

        self.users = {}
        for nom, prenom, nom_f, email, role, pwd in users_data:
            u = Utilisateur(
                nomUtilisateur=nom,
                prenom=prenom,
                nomFamille=nom_f,
                email=email,
                role=role,
                actif=True,
            )
            u.set_password(pwd)
            u.save()
            self.users[nom] = u

        self.stdout.write(f"  {len(self.users)} utilisateurs créés")

    # ------------------------------------------------------------------
    # LIEUX
    # ------------------------------------------------------------------
    def _create_lieux(self):
        from donnees.models import Lieu

        site = Lieu.objects.create(nomLieu="Site Industriel Nord", typeLieu="Site")
        bat_a = Lieu.objects.create(
            nomLieu="Bâtiment A - Production", typeLieu="Bâtiment", lieuParent=site
        )
        bat_b = Lieu.objects.create(
            nomLieu="Bâtiment B - Maintenance", typeLieu="Bâtiment", lieuParent=site
        )
        bat_c = Lieu.objects.create(
            nomLieu="Bâtiment C - Stockage", typeLieu="Bâtiment", lieuParent=site
        )

        self.lieux = {
            "atelier_prod": Lieu.objects.create(
                nomLieu="Atelier Production", typeLieu="Salle", lieuParent=bat_a
            ),
            "salle_chaud": Lieu.objects.create(
                nomLieu="Salle Chaudronnerie", typeLieu="Salle", lieuParent=bat_a
            ),
            "local_elec": Lieu.objects.create(
                nomLieu="Local Électrique", typeLieu="Local", lieuParent=bat_a
            ),
            "atelier_maint": Lieu.objects.create(
                nomLieu="Atelier Maintenance", typeLieu="Salle", lieuParent=bat_b
            ),
            "bureau_resp": Lieu.objects.create(
                nomLieu="Bureau Responsable", typeLieu="Bureau", lieuParent=bat_b
            ),
            "magasin_pces": Lieu.objects.create(
                nomLieu="Magasin Pièces", typeLieu="Entrepôt", lieuParent=bat_c
            ),
            "zone_stock": Lieu.objects.create(
                nomLieu="Zone Stockage Général", typeLieu="Entrepôt", lieuParent=bat_c
            ),
        }
        self.stdout.write(f"  {Lieu.objects.count()} lieux créés")

    # ------------------------------------------------------------------
    # FABRICANTS & FOURNISSEURS
    # ------------------------------------------------------------------
    def _create_fabricants_fournisseurs(self):
        from donnees.models import Adresse, Fabricant, Fournisseur

        def make_adresse(num, rue, ville, cp, pays):
            return Adresse.objects.create(
                numero=num, rue=rue, ville=ville, code_postal=cp, pays=pays
            )

        self.fabricants = {
            "siemens": Fabricant.objects.create(
                nom="Siemens AG",
                email="contact@siemens.com",
                numTelephone="+49 89 636 00",
                serviceApresVente=True,
                adresse=make_adresse(
                    "80", "Werner-von-Siemens-Str.", "Munich", "80333", "Allemagne"
                ),
            ),
            "schneider": Fabricant.objects.create(
                nom="Schneider Electric",
                email="contact@schneider-electric.com",
                numTelephone="+33 1 41 29 70 00",
                serviceApresVente=True,
                adresse=make_adresse(
                    "35", "Rue Joseph Monier", "Rueil-Malmaison", "92500", "France"
                ),
            ),
            "atlas": Fabricant.objects.create(
                nom="Atlas Copco",
                email="contact@atlascopco.com",
                numTelephone="+46 8 743 80 00",
                serviceApresVente=True,
            ),
            "grundfos": Fabricant.objects.create(
                nom="Grundfos",
                email="info@grundfos.com",
                numTelephone="+45 87 50 14 00",
                serviceApresVente=False,
            ),
        }

        self.fournisseurs = {
            "techni_pieces": Fournisseur.objects.create(
                nom="Techni-Pièces",
                email="commandes@techni-pieces.fr",
                numTelephone="04 72 00 12 34",
                serviceApresVente=True,
                adresse=make_adresse("12", "Avenue des Industries", "Lyon", "69007", "France"),
            ),
            "maintelec": Fournisseur.objects.create(
                nom="MaintelEC",
                email="pro@maintelec.fr",
                numTelephone="01 45 67 89 10",
                serviceApresVente=False,
                adresse=make_adresse("5", "Rue du Commerce", "Paris", "75015", "France"),
            ),
            "distrib_indus": Fournisseur.objects.create(
                nom="Distribution Industrielle SA",
                email="contact@di-sa.fr",
                numTelephone="03 20 11 22 33",
                serviceApresVente=True,
            ),
        }
        self.stdout.write(
            f"  {len(self.fabricants)} fabricants, {len(self.fournisseurs)} fournisseurs créés"
        )

    # ------------------------------------------------------------------
    # FAMILLES & MODÈLES D'ÉQUIPEMENT
    # ------------------------------------------------------------------
    def _create_familles_modeles(self):
        from equipement.models import FamilleEquipement, ModeleEquipement

        fam_elec = FamilleEquipement.objects.create(nom="Équipements électriques")
        fam_meca = FamilleEquipement.objects.create(nom="Équipements mécaniques")
        FamilleEquipement.objects.create(nom="Équipements fluidiques")
        FamilleEquipement.objects.create(nom="Moteurs électriques", familleParente=fam_elec)
        FamilleEquipement.objects.create(nom="Compresseurs", familleParente=fam_meca)

        self.modeles = {
            "variateur": ModeleEquipement.objects.create(
                nom="Variateur SINAMICS G120", fabricant=self.fabricants["siemens"]
            ),
            "automate": ModeleEquipement.objects.create(
                nom="Automate SIMATIC S7-1500", fabricant=self.fabricants["siemens"]
            ),
            "disjoncteur": ModeleEquipement.objects.create(
                nom="Disjoncteur NSX250B", fabricant=self.fabricants["schneider"]
            ),
            "compresseur": ModeleEquipement.objects.create(
                nom="Compresseur GA15 VSD+", fabricant=self.fabricants["atlas"]
            ),
            "pompe": ModeleEquipement.objects.create(
                nom="Pompe CM10-2", fabricant=self.fabricants["grundfos"]
            ),
        }
        self.stdout.write(f"  {len(self.modeles)} modèles d'équipement créés")

    # ------------------------------------------------------------------
    # ÉQUIPEMENTS
    # ------------------------------------------------------------------
    def _create_equipements(self):
        from equipement.models import Compteur, Equipement, FamilleEquipement, StatutEquipement

        resp = self.users["responsable.gmao"]
        now = timezone.now()
        fam_elec = FamilleEquipement.objects.get(nom="Équipements électriques")
        fam_meca = FamilleEquipement.objects.get(nom="Équipements mécaniques")
        fam_fluid = FamilleEquipement.objects.get(nom="Équipements fluidiques")

        equipements_data = [
            {
                "designation": "Variateur de fréquence VF-01",
                "numSerie": "SIE-VF-2021-001",
                "reference": "REF-VF-001",
                "lieu": self.lieux["atelier_prod"],
                "modele": self.modeles["variateur"],
                "fabricant": self.fabricants["siemens"],
                "fournisseur": self.fournisseurs["techni_pieces"],
                "famille": fam_elec,
                "dateMiseEnService": now - timedelta(days=900),
                "prixAchat": 2850.00,
                "statut": "EN_FONCTIONNEMENT",
            },
            {
                "designation": "Automate programmable AP-02",
                "numSerie": "SIE-AP-2020-007",
                "reference": "REF-AP-002",
                "lieu": self.lieux["local_elec"],
                "modele": self.modeles["automate"],
                "fabricant": self.fabricants["siemens"],
                "fournisseur": self.fournisseurs["maintelec"],
                "famille": fam_elec,
                "dateMiseEnService": now - timedelta(days=1200),
                "prixAchat": 5400.00,
                "statut": "EN_FONCTIONNEMENT",
            },
            {
                "designation": "Compresseur d'air CA-01",
                "numSerie": "AC-GA15-2019-042",
                "reference": "REF-CA-001",
                "lieu": self.lieux["atelier_maint"],
                "modele": self.modeles["compresseur"],
                "fabricant": self.fabricants["atlas"],
                "fournisseur": self.fournisseurs["distrib_indus"],
                "famille": fam_meca,
                "dateMiseEnService": now - timedelta(days=1800),
                "prixAchat": 8200.00,
                "statut": "EN_FONCTIONNEMENT",
            },
            {
                "designation": "Pompe de circulation PC-03",
                "numSerie": "GF-CM10-2022-015",
                "reference": "REF-PC-003",
                "lieu": self.lieux["salle_chaud"],
                "modele": self.modeles["pompe"],
                "fabricant": self.fabricants["grundfos"],
                "fournisseur": self.fournisseurs["techni_pieces"],
                "famille": fam_fluid,
                "dateMiseEnService": now - timedelta(days=600),
                "prixAchat": 1350.00,
                "statut": "DEGRADE",
            },
            {
                "designation": "Tableau de distribution TD-01",
                "numSerie": "SCH-NSX-2021-088",
                "reference": "REF-TD-001",
                "lieu": self.lieux["local_elec"],
                "modele": self.modeles["disjoncteur"],
                "fabricant": self.fabricants["schneider"],
                "fournisseur": self.fournisseurs["maintelec"],
                "famille": fam_elec,
                "dateMiseEnService": now - timedelta(days=1500),
                "prixAchat": 3200.00,
                "statut": "EN_FONCTIONNEMENT",
            },
            {
                "designation": "Pompe hydraulique PH-04",
                "numSerie": "GF-CM10-2018-003",
                "reference": "REF-PH-004",
                "lieu": self.lieux["atelier_prod"],
                "modele": self.modeles["pompe"],
                "fabricant": self.fabricants["grundfos"],
                "fournisseur": self.fournisseurs["distrib_indus"],
                "famille": fam_fluid,
                "dateMiseEnService": now - timedelta(days=2400),
                "prixAchat": 1100.00,
                "statut": "A_LARRET",
            },
        ]

        self.equipements = {}
        for data in equipements_data:
            statut = data.pop("statut")
            eq = Equipement.objects.create(createurEquipement=resp, **data)
            StatutEquipement.objects.create(equipement=eq, statut=statut)
            self.equipements[eq.numSerie] = eq

        # Compteurs
        Compteur.objects.create(
            nomCompteur="Heures de fonctionnement",
            valeurCourante=4320,
            unite="heures",
            estPrincipal=True,
            type="Général",
            equipement=self.equipements["SIE-VF-2021-001"],
        )
        Compteur.objects.create(
            nomCompteur="Heures moteur",
            valeurCourante=9800,
            unite="heures",
            estPrincipal=True,
            type="Général",
            equipement=self.equipements["AC-GA15-2019-042"],
        )
        Compteur.objects.create(
            nomCompteur="Cycles de démarrage",
            valeurCourante=1240,
            unite="cycles",
            estPrincipal=False,
            type="Général",
            equipement=self.equipements["AC-GA15-2019-042"],
        )

        self.stdout.write(f"  {len(self.equipements)} équipements créés")

    # ------------------------------------------------------------------
    # CONSOMMABLES, MAGASINS & STOCKS
    # ------------------------------------------------------------------
    def _create_consommables_magasins(self):
        from stock.models import Consommable, Magasin, PorterSur, Stocker

        # Magasins
        mag_central = Magasin.objects.create(nom="Magasin Central", estMobile=False)
        mag_mobile = Magasin.objects.create(nom="Magasin Mobile Atelier", estMobile=True)
        mag_elec = Magasin.objects.create(nom="Armoire Électrique", estMobile=False)
        self.magasins = {
            "central": mag_central,
            "mobile": mag_mobile,
            "elec": mag_elec,
        }

        # Consommables
        consommables_data = [
            ("Filtre à air compresseur", 50, 10),
            ("Huile hydraulique ISO VG 46", 30, 5),
            ("Courroie trapézoïdale A42", 20, 3),
            ("Joint torique 50x3", 100, 20),
            ("Fusible 16A type gG", 150, 30),
            ("Relais thermique 10-16A", 40, 8),
            ("Roulement 6205-2RS", 60, 10),
            ("Câble souple 2.5mm² (m)", 200, 50),
        ]

        self.consommables = []
        today = timezone.now().date()
        today.isoformat()

        for nom, qte_central, qte_mobile in consommables_data:
            c = Consommable.objects.create(designation=nom, seuilStockFaible=5)
            self.consommables.append(c)

            # Stock magasin central
            Stocker.objects.create(consommable=c, magasin=mag_central, quantite=qte_central)
            # Stock magasin mobile
            Stocker.objects.create(consommable=c, magasin=mag_mobile, quantite=qte_mobile)

            # Historique d'achat
            PorterSur.objects.create(
                consommable=c,
                fournisseur=self.fournisseurs["techni_pieces"],
                fabricant=list(self.fabricants.values())[0],
                quantite=qte_central + qte_mobile + 20,
                prix_unitaire=round(random.uniform(5, 150), 2),
                date_reference_prix=timezone.now() - timedelta(days=random.randint(10, 200)),
            )

        # Armoire électrique : que les fusibles et relais
        Stocker.objects.create(consommable=self.consommables[4], magasin=mag_elec, quantite=80)
        Stocker.objects.create(consommable=self.consommables[5], magasin=mag_elec, quantite=15)

        self.stdout.write(
            f"  {len(self.consommables)} consommables, {Magasin.objects.count()} magasins créés"
        )

    # ------------------------------------------------------------------
    # DEMANDES D'INTERVENTION & BONS DE TRAVAIL
    # ------------------------------------------------------------------
    def _create_di_bt(self):
        from maintenance.models import BonTravail, DemandeIntervention

        now = timezone.now()
        op1 = self.users["o.durand"]
        op2 = self.users["s.leroy"]
        resp = self.users["responsable.gmao"]
        tech1 = self.users["t.martin"]
        tech2 = self.users["a.bernard"]
        tech3 = self.users["l.moreau"]
        tech4 = self.users["c.camille"]

        list(self.equipements.values())

        di_bt_scenarios = [
            # --- BT clôturé (panne résolue) ---
            {
                "di": {
                    "nom": "Vibrations anormales pompe PC-03",
                    "commentaire": "La pompe émet des vibrations inhabituelles depuis ce matin.",
                    "statut": "TRANSFORMEE",
                    "statut_suppose": "DEGRADE",
                    "utilisateur": op1,
                    "equipement": self.equipements["GF-CM10-2022-015"],
                    "date_creation": now - timedelta(days=30),
                    "date_changementStatut": now - timedelta(days=29),
                },
                "bt": {
                    "nom": "Remplacement roulement pompe PC-03",
                    "type": "CORRECTIF",
                    "statut": "CLOTURE",
                    "date_assignation": now - timedelta(days=29),
                    "date_debut": now - timedelta(days=28),
                    "date_fin": now - timedelta(days=27),
                    "date_cloture": now - timedelta(days=25),
                    "date_prevue": now - timedelta(days=27),
                    "diagnostic": "Roulement avant usé. Remplacement effectué.",
                    "techniciens": [tech1, tech3],
                    "responsable": resp,
                },
            },
            # --- BT en cours ---
            {
                "di": {
                    "nom": "Arrêt compresseur CA-01 - surpression",
                    "commentaire": "Le compresseur s'est arrêté en alarme surpression à 8h30.",
                    "statut": "TRANSFORMEE",
                    "statut_suppose": "A_LARRET",
                    "utilisateur": op2,
                    "equipement": self.equipements["AC-GA15-2019-042"],
                    "date_creation": now - timedelta(days=5),
                    "date_changementStatut": now - timedelta(days=5),
                },
                "bt": {
                    "nom": "Diagnostic et remise en service compresseur CA-01",
                    "type": "CORRECTIF",
                    "statut": "EN_COURS",
                    "date_assignation": now - timedelta(days=4),
                    "date_debut": now - timedelta(days=3),
                    "date_fin": None,
                    "date_prevue": now + timedelta(days=1),
                    "diagnostic": "Vanne de décharge défectueuse. Commande pièce en cours.",
                    "techniciens": [tech2, tech4],
                    "responsable": resp,
                },
            },
            # --- BT en attente ---
            {
                "di": {
                    "nom": "Défaut communication variateur VF-01",
                    "commentaire": "Le variateur affiche une alarme de communication réseau.",
                    "statut": "TRANSFORMEE",
                    "statut_suppose": "DEGRADE",
                    "utilisateur": op1,
                    "equipement": self.equipements["SIE-VF-2021-001"],
                    "date_creation": now - timedelta(days=2),
                    "date_changementStatut": now - timedelta(days=2),
                },
                "bt": {
                    "nom": "Contrôle câblage Profinet variateur VF-01",
                    "type": "CORRECTIF",
                    "statut": "EN_ATTENTE",
                    "date_assignation": now - timedelta(days=1),
                    "date_debut": None,
                    "date_fin": None,
                    "date_prevue": now + timedelta(days=2),
                    "diagnostic": None,
                    "techniciens": [tech1],
                    "responsable": resp,
                },
            },
            # --- DI acceptée sans BT ---
            {
                "di": {
                    "nom": "Fuite huile tableau de distribution TD-01",
                    "commentaire": "Une légère fuite d'huile de condensateur visible sur le bas du tableau.",
                    "statut": "ACCEPTEE",
                    "statut_suppose": "DEGRADE",
                    "utilisateur": op2,
                    "equipement": self.equipements["SCH-NSX-2021-088"],
                    "date_creation": now - timedelta(days=1),
                    "date_changementStatut": now - timedelta(hours=3),
                },
                "bt": None,
            },
            # --- DI en attente (soumise aujourd'hui) ---
            {
                "di": {
                    "nom": "Bruit suspect pompe hydraulique PH-04",
                    "commentaire": "Claquement métallique lors des démarrages. Pompe à l'arrêt par mesure de sécurité.",
                    "statut": "EN_ATTENTE",
                    "statut_suppose": "A_LARRET",
                    "utilisateur": op1,
                    "equipement": self.equipements["GF-CM10-2018-003"],
                    "date_creation": now - timedelta(hours=2),
                    "date_changementStatut": now - timedelta(hours=2),
                },
                "bt": None,
            },
            # --- BT terminé (attente clôture) ---
            {
                "di": {
                    "nom": "Échauffement anormal automate AP-02",
                    "commentaire": "Température boîtier > 60°C. Ventilateur interne bruyant.",
                    "statut": "TRANSFORMEE",
                    "statut_suppose": "DEGRADE",
                    "utilisateur": op2,
                    "equipement": self.equipements["SIE-AP-2020-007"],
                    "date_creation": now - timedelta(days=10),
                    "date_changementStatut": now - timedelta(days=10),
                },
                "bt": {
                    "nom": "Remplacement ventilateur automate AP-02",
                    "type": "CORRECTIF",
                    "statut": "TERMINE",
                    "date_assignation": now - timedelta(days=9),
                    "date_debut": now - timedelta(days=8),
                    "date_fin": now - timedelta(days=7),
                    "date_prevue": now - timedelta(days=7),
                    "date_cloture": None,
                    "diagnostic": "Ventilateur 24V DC HS. Remplacé par pièce neuve du stock.",
                    "techniciens": [tech3],
                    "responsable": resp,
                },
            },
            # --- DI refusée ---
            {
                "di": {
                    "nom": "Peinture écaillée sur capot compresseur",
                    "commentaire": "Aspect esthétique dégradé, pas de problème fonctionnel.",
                    "statut": "REFUSEE",
                    "statut_suppose": "EN_FONCTIONNEMENT",
                    "utilisateur": op1,
                    "equipement": self.equipements["AC-GA15-2019-042"],
                    "date_creation": now - timedelta(days=15),
                    "date_changementStatut": now - timedelta(days=14),
                },
                "bt": None,
            },
            # --- BT préventif planifié ---
            {
                "di": {
                    "nom": "Maintenance préventive annuelle compresseur CA-01",
                    "commentaire": "Maintenance planifiée : vidange huile, contrôle courroies, filtre.",
                    "statut": "TRANSFORMEE",
                    "statut_suppose": "EN_FONCTIONNEMENT",
                    "utilisateur": resp,
                    "equipement": self.equipements["AC-GA15-2019-042"],
                    "date_creation": now - timedelta(days=45),
                    "date_changementStatut": now - timedelta(days=45),
                },
                "bt": {
                    "nom": "Maintenance préventive annuelle CA-01",
                    "type": "PREVENTIF",
                    "statut": "EN_ATTENTE",
                    "date_assignation": now - timedelta(days=44),
                    "date_debut": None,
                    "date_fin": None,
                    "date_prevue": now + timedelta(days=7),
                    "diagnostic": None,
                    "techniciens": [tech1, tech2],
                    "responsable": resp,
                },
            },
        ]

        nb_di = 0
        nb_bt = 0
        for scenario in di_bt_scenarios:
            di_data = scenario["di"]
            bt_data = scenario["bt"]

            # Le numero de DI suit le meme format DI-XXXX que celui genere
            # automatiquement a la creation depuis l'application (FailureForm.vue).
            # Le titre descriptif d'origine est conserve dans le commentaire.
            numero_di = f"DI-{str(nb_di + 1).zfill(4)}"
            titre = di_data["nom"]
            commentaire_origine = di_data.get("commentaire", "")
            commentaire_final = f"{titre}\n{commentaire_origine}".strip()

            di = DemandeIntervention.objects.create(
                nom=numero_di,
                commentaire=commentaire_final,
                statut=di_data["statut"],
                statut_suppose=di_data["statut_suppose"],
                utilisateur=di_data["utilisateur"],
                equipement=di_data["equipement"],
                date_creation=di_data["date_creation"],
                date_changementStatut=di_data["date_changementStatut"],
            )
            nb_di += 1

            if bt_data:
                bt = BonTravail.objects.create(
                    nom=bt_data["nom"],
                    type=bt_data["type"],
                    statut=bt_data["statut"],
                    date_assignation=bt_data.get("date_assignation"),
                    date_debut=bt_data.get("date_debut"),
                    date_fin=bt_data.get("date_fin"),
                    date_cloture=bt_data.get("date_cloture"),
                    date_prevue=bt_data.get("date_prevue"),
                    diagnostic=bt_data.get("diagnostic"),
                    demande_intervention=di,
                    responsable=bt_data.get("responsable"),
                )
                if bt_data.get("techniciens"):
                    bt.utilisateur_assigne.set(bt_data["techniciens"])
                nb_bt += 1

        self.stdout.write(f"  {nb_di} DI, {nb_bt} BT créés")

    # ------------------------------------------------------------------
    # RÉSUMÉ
    # ------------------------------------------------------------------
    def _print_summary(self):

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("╔══════════════════════════════════════╗"))
        self.stdout.write(self.style.SUCCESS("║       COMPTES UTILISATEURS TP        ║"))
        self.stdout.write(self.style.SUCCESS("╠══════════════════════════════════════╣"))
        accounts = [
            ("responsable.gmao", "Responsable1!", "Responsable GMAO"),
            ("t.martin", "Technicien1!", "Technicien prod"),
            ("a.bernard", "Technicien1!", "Technicien prod"),
            ("l.moreau", "Technicien1!", "Technicien prod"),
            ("c.camille", "Technicien1!", "Technicien prod"),
            ("o.durand", "Operateur1!", "Opérateur prod"),
            ("s.leroy", "Operateur1!", "Opérateur prod"),
            ("mag.simon", "Magasinier1!", "Magasinier"),
        ]
        for login, pwd, role in accounts:
            line = f"  {login:<16} {pwd:<18} {role}"
            self.stdout.write(line)
        self.stdout.write(self.style.SUCCESS("╚══════════════════════════════════════╝"))
        self.stdout.write("")
