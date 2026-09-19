# Structure : nom_permission -> (description, type, permission_parente)
# type : 'affichage' | 'action'
# permission_parente : nom de la permission prérequise (str) ou None
#
# Règle : cocher un enfant coche automatiquement son parent (et ses ancêtres).
# Exemple : cocher di:archive coche di:viewDetail puis di:viewList.

perms = {
    # ── Demandes d'intervention ──────────────────────────────────────────────
    'di:viewList':    ("Voir la liste des demandes d'intervention",              'affichage', None),
    'di:viewDetail':  ("Voir le détail d'une demande d'intervention",            'affichage', 'di:viewList'),
    'di:create':      ("Créer une demande d'intervention",                       'action',    'di:viewList'),
    'di:editAll':     ("Modifier toutes les demandes d'intervention",            'action',    'di:viewDetail'),
    'di:editCreated': ("Modifier ses propres demandes d'intervention",           'action',    'di:viewDetail'),
    'di:delete':      ("Supprimer une demande d'intervention",                   'action',    'di:viewDetail'),
    'di:accept':      ("Accepter une demande d'intervention",                    'action',    'di:viewDetail'),
    'di:refuse':      ("Refuser une demande d'intervention",                     'action',    'di:viewDetail'),
    'di:transform':   ("Transformer une demande d'intervention en bon de travail",'action',   'di:viewDetail'),
    'di:export':      ("Exporter les demandes d'intervention",                   'action',    'di:viewList'),
    'di:archive':     ("Archiver une demande d'intervention",                    'action',    'di:viewDetail'),

    # ── Bons de travail ──────────────────────────────────────────────────────
    'bt:viewList':               ("Voir la liste des bons de travail",              'affichage', None),
    'bt:viewDetail':             ("Voir le détail d'un bon de travail",             'affichage', 'bt:viewList'),
    'bt:create':                 ("Créer un bon de travail",                        'action',    'bt:viewList'),
    'bt:editAll':                ("Modifier tous les bons de travail",              'action',    'bt:viewDetail'),
    'bt:editAssigned':           ("Modifier les bons de travail assignés",          'action',    'bt:viewDetail'),
    'bt:delete':                 ("Supprimer un bon de travail",                    'action',    'bt:viewDetail'),
    'bt:start':                  ("Démarrer un bon de travail",                     'action',    'bt:viewDetail'),
    'bt:end':                    ("Clôturer un bon de travail",                     'action',    'bt:viewDetail'),
    'bt:refuse':                 ("Refuser un bon de travail",                      'action',    'bt:viewDetail'),
    'bt:refuseClosure':          ("Refuser la clôture d'un bon de travail",         'action',    'bt:viewDetail'),
    'bt:acceptClosure':          ("Accepter la clôture d'un bon de travail",        'action',    'bt:viewDetail'),
    'bt:acceptConsumableRequest':("Valider une demande de consommable",             'action',    'bt:viewDetail'),
    'bt:export':                 ("Exporter les bons de travail",                   'action',    'bt:viewList'),
    'bt:archive':                ("Archiver un bon de travail",                     'action',    'bt:viewDetail'),

    # ── Équipements ──────────────────────────────────────────────────────────
    'eq:viewList':      ("Voir la liste des équipements",                       'affichage', None),
    'eq:viewDetail':    ("Voir le détail d'un équipement",                      'affichage', 'eq:viewList'),
    'eq:view.calendar': ("Voir le calendrier des maintenances d'un équipement", 'affichage', 'eq:viewDetail'),
    'eq:create':        ("Créer un équipement",                                 'action',    'eq:viewList'),
    'eq:edit':          ("Modifier un équipement",                              'action',    'eq:viewDetail'),
    'eq:delete':        ("Supprimer un équipement",                             'action',    'eq:viewDetail'),
    'eq:export':        ("Exporter les équipements",                            'action',    'eq:viewList'),
    'eq:archive':       ("Archiver un équipement",                              'action',    'eq:viewDetail'),
    'eq:document.add':   ("Ajouter un document à un équipement",                'action',    'eq:viewDetail'),
    'eq:document.delete':("Supprimer un document d'un équipement",              'action',    'eq:viewDetail'),
    'eq:kpi.view':        ("Voir les indicateurs KPI de maintenance d'un équipement",  'affichage', 'eq:viewDetail'),
    'eq:historique.view': ("Voir l'historique des états d'un équipement",              'affichage', 'eq:viewDetail'),

    # ── Compteurs ────────────────────────────────────────────────────────────
    'cp:viewList':   ("Voir la liste des compteurs",    'affichage', None),
    'cp:viewDetail': ("Voir le détail d'un compteur",   'affichage', 'cp:viewList'),
    'cp:create':     ("Créer un compteur",              'action',    'cp:viewList'),
    'cp:edit':       ("Modifier un compteur",           'action',    'cp:viewDetail'),
    'cp:delete':     ("Supprimer un compteur",          'action',    'cp:viewDetail'),
    'cp:export':     ("Exporter les compteurs",         'action',    'cp:viewList'),

    # ── Maintenance préventive ───────────────────────────────────────────────
    'mp:viewList':   ("Voir la liste des maintenances préventives",  'affichage', None),
    'mp:viewDetail': ("Voir le détail d'une maintenance préventive", 'affichage', 'mp:viewList'),
    'mp:calendar':   ("Voir le calendrier des maintenances préventives", 'affichage', 'mp:viewList'),
    'mp:create':     ("Créer une maintenance préventive",            'action',    'mp:viewList'),
    'mp:edit':       ("Modifier une maintenance préventive",         'action',    'mp:viewDetail'),
    'mp:delete':     ("Supprimer une maintenance préventive",        'action',    'mp:viewDetail'),
    'mp:export':     ("Exporter les maintenances préventives",       'action',    'mp:viewList'),

    # ── Stocks ───────────────────────────────────────────────────────────────
    'stock:view':             ("Voir les stocks",                           'affichage', None),
    'stock:viewReservations': ("Voir les mises de côté",                    'affichage', 'stock:view'),
    'stock:export':           ("Exporter les stocks",                       'action',    'stock:view'),
    'stock:addPurchase':      ("Enregistrer un achat",                      'action',    'stock:view'),
    'stock:transfer':         ("Transférer du stock entre magasins",        'action',    'stock:view'),

    # ── Consommables ─────────────────────────────────────────────────────────
    'cons:viewDetail': ("Voir le détail d'un consommable",  'affichage', None),
    'cons:create':     ("Créer un consommable",             'action',    'cons:viewDetail'),
    'cons:edit':       ("Modifier un consommable",          'action',    'cons:viewDetail'),
    'cons:delete':     ("Supprimer un consommable",         'action',    'cons:viewDetail'),
    'cons:export':     ("Exporter les consommables",        'action',    'cons:viewDetail'),
    'cons:archive':    ("Archiver un consommable",          'action',    'cons:viewDetail'),

    # ── Magasins ─────────────────────────────────────────────────────────────
    'mag:viewList':   ("Voir la liste des magasins",    'affichage', None),
    'mag:viewDetail': ("Voir le détail d'un magasin",   'affichage', 'mag:viewList'),
    'mag:create':     ("Créer un magasin",              'action',    'mag:viewList'),
    'mag:edit':       ("Modifier un magasin",           'action',    'mag:viewDetail'),
    'mag:delete':     ("Supprimer un magasin",          'action',    'mag:viewDetail'),
    'mag:export':     ("Exporter les magasins",         'action',    'mag:viewList'),
    'mag:archive':    ("Archiver un magasin",           'action',    'mag:viewDetail'),

    # ── Utilisateurs ─────────────────────────────────────────────────────────
    'user:viewList':   ("Voir la liste des utilisateurs",   'affichage', None),
    'user:viewDetail': ("Voir le détail d'un utilisateur",  'affichage', 'user:viewList'),
    'user:create':     ("Créer un utilisateur",             'action',    'user:viewList'),
    'user:edit':       ("Modifier un utilisateur",          'action',    'user:viewDetail'),
    'user:disable':    ("Désactiver un utilisateur",        'action',    'user:viewDetail'),
    'user:enable':     ("Activer un utilisateur",           'action',    'user:viewDetail'),
    'user:delete':     ("Supprimer un utilisateur",         'action',    'user:viewDetail'),
    'user:export':     ("Exporter les utilisateurs",        'action',    'user:viewList'),

    # ── Rôles ────────────────────────────────────────────────────────────────
    'role:viewList':   ("Voir la liste des rôles",   'affichage', None),
    'role:viewDetail': ("Voir le détail d'un rôle",  'affichage', 'role:viewList'),
    'role:create':     ("Créer un rôle",             'action',    'role:viewList'),
    'role:edit':       ("Modifier un rôle",          'action',    'role:viewDetail'),
    'role:delete':     ("Supprimer un rôle",         'action',    'role:viewDetail'),
    'role:export':     ("Exporter les rôles",        'action',    'role:viewList'),

    # ── Lieux ────────────────────────────────────────────────────────────────
    'loc:viewList':   ("Voir la liste des lieux",   'affichage', None),
    'loc:viewDetail': ("Voir le détail d'un lieu",  'affichage', 'loc:viewList'),
    'loc:create':     ("Créer un lieu",             'action',    'loc:viewList'),
    'loc:edit':       ("Modifier un lieu",          'action',    'loc:viewDetail'),
    'loc:delete':     ("Supprimer un lieu",         'action',    'loc:viewDetail'),
    'loc:export':     ("Exporter les lieux",        'action',    'loc:viewList'),
    'loc:archive':    ("Archiver un lieu",          'action',    'loc:viewDetail'),

    # ── Fournisseurs ─────────────────────────────────────────────────────────
    'sup:viewList':   ("Voir la liste des fournisseurs",   'affichage', None),
    'sup:viewDetail': ("Voir le détail d'un fournisseur",  'affichage', 'sup:viewList'),
    'sup:create':     ("Créer un fournisseur",             'action',    'sup:viewList'),
    'sup:edit':       ("Modifier un fournisseur",          'action',    'sup:viewDetail'),
    'sup:delete':     ("Supprimer un fournisseur",         'action',    'sup:viewDetail'),
    'sup:export':     ("Exporter les fournisseurs",        'action',    'sup:viewList'),
    'sup:archive':    ("Archiver un fournisseur",          'action',    'sup:viewDetail'),

    # ── Fabricants ───────────────────────────────────────────────────────────
    'man:viewList':   ("Voir la liste des fabricants",   'affichage', None),
    'man:viewDetail': ("Voir le détail d'un fabricant",  'affichage', 'man:viewList'),
    'man:create':     ("Créer un fabricant",             'action',    'man:viewList'),
    'man:edit':       ("Modifier un fabricant",          'action',    'man:viewDetail'),
    'man:delete':     ("Supprimer un fabricant",         'action',    'man:viewDetail'),
    'man:export':     ("Exporter les fabricants",        'action',    'man:viewList'),
    'man:archive':    ("Archiver un fabricant",          'action',    'man:viewDetail'),

    # ── Modèles d'équipement ─────────────────────────────────────────────────
    'eqmod:viewList':   ("Voir la liste des modèles d'équipement",   'affichage', None),
    'eqmod:viewDetail': ("Voir le détail d'un modèle d'équipement",  'affichage', 'eqmod:viewList'),
    'eqmod:create':     ("Créer un modèle d'équipement",             'action',    'eqmod:viewList'),
    'eqmod:edit':       ("Modifier un modèle d'équipement",          'action',    'eqmod:viewDetail'),
    'eqmod:delete':     ("Supprimer un modèle d'équipement",         'action',    'eqmod:viewDetail'),
    'eqmod:export':     ("Exporter les modèles d'équipement",        'action',    'eqmod:viewList'),
    'eqmod:archive':    ("Archiver un modèle d'équipement",          'action',    'eqmod:viewDetail'),

    # ── Véhicules (flotte) ───────────────────────────────────────────────────
    'veh:viewList':   ("Voir la liste des véhicules",    'affichage', None),
    'veh:viewDetail': ("Voir le détail d'un véhicule",   'affichage', 'veh:viewList'),
    'veh:create':     ("Créer un véhicule",              'action',    'veh:viewList'),
    'veh:edit':       ("Modifier un véhicule",           'action',    'veh:viewDetail'),
    'veh:delete':     ("Supprimer un véhicule",          'action',    'veh:viewDetail'),
    'veh:export':     ("Exporter les véhicules",         'action',    'veh:viewList'),
    'veh:archive':    ("Archiver un véhicule",           'action',    'veh:viewDetail'),

    # ── Export global ────────────────────────────────────────────────────────
    'export:view': ("Accéder aux exports de données", 'affichage', None),
    'export:eq': ("Exporter les équipements", 'action', 'export:view'),
    'export:eqstatus': ("Exporter les statuts des équipements", 'action', 'export:view'),
    'export:bt': ("Exporter les bons de travail", 'action', 'export:view'),
    'export:di': ("Exporter les demandes d'intervention", 'action', 'export:view'),
    'export:cons': ("Exporter les consommables", 'action', 'export:view'),
    'export:histcons': ("Exporter l'historique des achats de consommables", 'action', 'export:view'),
    'export:stockmag': ("Exporter les stocks des magasins", 'action', 'export:view'),
    'export:mag': ("Exporter les magasins", 'action', 'export:view'),
    'export:histmag': ("Exporter l'historique des sorties de magasins", 'action', 'export:view'),
    'export:logs': ("Exporter l'historique des logs", 'action', 'export:view'),
    'export:sup': ("Exporter les fournisseurs", 'action', 'export:view'),
    'export:man': ("Exporter les fabricants", 'action', 'export:view'),
    'export:eqmod': ("Exporter les modèles d'équipement", 'action', 'export:view'),
    'export:lieu': ("Exporter les lieux", 'action', 'export:view'),
    'export:cp': ("Exporter les compteurs numériques", 'action', 'export:view'),
    'export:seuils': ("Exporter les seuils de compteurs", 'action', 'export:view'),
    'export:periodicites': ("Exporter les périodicités", 'action', 'export:view'),
    'export:user': ("Exporter les utilisateurs", 'action', 'export:view'),

    # ── Menu ─────────────────────────────────────────────────────────────────
    'menu:view':           ("Accéder au menu de navigation",         'affichage', None),
    'menu:dataManagement': ("Accéder au menu de gestion des données",'affichage', None),
    'menu:calendar':       ("Accéder au calendrier",                 'affichage', None),

    # ── Dashboard ────────────────────────────────────────────────────────────
    'dash:display.di':         ("Afficher les demandes d'intervention sur le tableau de bord", 'affichage', None),
    'dash:display.diCreated':  ("Afficher ses demandes d'intervention sur le tableau de bord", 'affichage', None),
    'dash:display.bt':         ("Afficher les bons de travail sur le tableau de bord",         'affichage', None),
    'dash:display.btAssigned': ("Afficher ses bons de travail assignés sur le tableau de bord",'affichage', None),
    'dash:display.eq':         ("Afficher les équipements sur le tableau de bord",             'affichage', None),
    'dash:display.mag':        ("Afficher les magasins sur le tableau de bord",                'affichage', None),
    'dash:display.vertical':   ("Afficher le tableau de bord en mode vertical",               'affichage', None),
    'dash:stats.full':         ("Voir toutes les statistiques",                               'affichage', None),
    'dash:stats.bt':           ("Voir les statistiques des bons de travail",                  'affichage', None),
    'dash:stats.di':           ("Voir les statistiques des demandes d'intervention",          'affichage', None),
}

perms_map = {
    "Responsable GMAO": [
        perm for perm in perms.keys() if perm not in [
            'dash:display.vertical', 'dash:display.eq', 'dash:display.mag',
            'dash:display.btAssigned', 'dash:display.diCreated',
        ]
    ],

    "Technicien prod": [
        'di:viewList', 'di:viewDetail', 'di:create', 'di:editCreated',
        'bt:viewList', 'bt:viewDetail', 'bt:start', 'bt:end', 'bt:editAssigned',
        'eq:viewList', 'eq:viewDetail', 'eq:edit', 'eq:document.add',
        'veh:viewList', 'veh:viewDetail',
        'cp:viewList', 'cp:viewDetail', 'cp:edit',
        'mp:viewList', 'mp:viewDetail',
        'stock:view',
        'menu:view',
        'dash:display.eq', 'dash:display.btAssigned', 'dash:stats.bt',
    ],

    "Technicien maintenance": [
        'di:viewList', 'di:viewDetail', 'di:create', 'di:editCreated',
        'bt:viewList', 'bt:viewDetail', 'bt:start', 'bt:end', 'bt:editAssigned',
        'eq:viewList', 'eq:viewDetail', 'eq:edit', 'eq:document.add',
        'eq:view.calendar',
        'veh:viewList', 'veh:viewDetail', 'veh:edit',
        'cp:viewList', 'cp:viewDetail', 'cp:edit',
        'mp:viewList', 'mp:viewDetail', 'mp:create', 'mp:edit',
        'stock:view',
        'menu:view',
        'dash:display.eq', 'dash:display.btAssigned', 'dash:stats.bt',
    ],

    "Opérateur prod": [
        'di:viewList', 'di:viewDetail', 'di:create', 'di:editCreated',
        'bt:viewList', 'bt:viewDetail',
        'eq:viewList', 'eq:viewDetail',
        'veh:viewList', 'veh:viewDetail',
        'dash:display.diCreated', 'dash:display.eq', 'dash:stats.di','dash:display.vertical',
    ],

    "Magasinier": [
        'bt:viewList', 'bt:viewDetail', 'bt:acceptConsumableRequest',
        'stock:view', 'stock:export', 'stock:viewReservations', 'stock:addPurchase', 'stock:transfer',
        'cons:viewDetail', 'cons:create', 'cons:edit', 'cons:delete', 'cons:export',
        'mag:viewList', 'mag:viewDetail', 'mag:create', 'mag:edit', 'mag:delete', 'mag:export',
        'dash:display.mag',
    ],
}
