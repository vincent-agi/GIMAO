import { createRouter, createWebHistory } from 'vue-router'

// Utils
import store, { checkAuthValidity } from '@/store'

const routes = [
  // Auth routes (publiques)
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Auth/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/set-password',
    name: 'SetPassword',
    component: () => import('@/views/Auth/SetPassword.vue'),
    meta: { public: true }
  },

  // Routes protégées
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard/Dashboard.vue'),
    meta: { title: 'Tableau de Bord' }
  },
  //  ROLES ET PERMISSIONS
  {
    path: '/RoleList',
    name: 'RoleList',
    component: () => import('@/views/Users/RoleList.vue'),
    meta: { title: 'Gestion des rôles', requiresPermissions: ['role:viewList'] }
  },
  {
    path: '/UserPermissions/:id',
    name: 'UserPermissions',
    component: () => import('@/views/Users/UserPermissions.vue'),
    props: true,
    meta: { title: 'Permissions utilisateur', requiresPermissions: ['user:edit'] }
  },
  // 

  {
    path: '/UserList',
    name: 'UserList',
    component: () => import('@/views/Users/UserList.vue'),
    meta: {
      title: 'Gestion des Comptes',
      requiresPermissions: ['user:viewList']
    }
  },

  {
    path: '/UserDetail/:id',
    name: 'UserDetail',
    component: () => import('@/views/Users/UserDetail.vue'),
    props: true,
    meta: {
      title: 'Afficher un utilisateur',
      requiresPermissions: ['user:viewDetail'],
      checksIfSelf: true
    }
  },

  {
    path: '/EditUser/:id',
    name: 'EditUser',
    component: () => import('@/views/Users/EditUser.vue'),
    props: true,
    meta: { title: 'Modifier un utilisateur', requiresPermissions: ['user:edit'], checksIfSelf: true }
  },

  {
    path: '/CreateUser',
    name: 'CreateUser',
    component: () => import('@/views/Users/CreateUser.vue'),
    meta: { title: 'Créer un utilisateur', requiresPermissions: ['user:create'] }
  },

  // Stocks & Consommables --------------------------------------------------------

  {
    path: '/stocks',
    name: 'Stocks',
    component: () => import('@/views/Stocks/Stocks.vue'),
    meta: { title: 'Stocks', requiresPermissions: ['stock:view'] }
  },

  {
    path: '/CreateConsumable',
    name: 'CreateConsumable',
    component: () => import('@/views/Stocks/CreateConsumable.vue'),
    meta: { title: 'Créer un consommable', requiresPermissions: ['cons:create'] }
  },

  {
    path: '/EditConsumable/:id',
    name: 'EditConsumable',
    component: () => import('@/views/Stocks/EditConsumable.vue'),
    props: true,
    meta: { title: 'Modifier un consommable', requiresPermissions: ['cons:edit'] }
  },

  {
    path: '/Consumable/:id',
    name: 'ConsumableDetail',
    component: () => import('@/views/Stocks/ConsumableDetail.vue'),
    props: true,
    meta: { title: 'Détails du consommable', requiresPermissions: ['cons:viewDetail'] }
  },

  {
    path: '/DeleteConsumable/:id',
    name: 'DeleteConsumable',
    component: () => import('@/views/Stocks/CreateConsumable.vue'),
    props: true,
    meta: { title: 'Supprimer un consommable', requiresPermissions: ['cons:delete'] }
  },

  // Magasins
  {
    path: '/MagasinList',
    name: 'MagasinList',
    component: () => import('@/views/Stocks/Stocks.vue'),
    meta: { title: 'Magasins', requiresPermissions: ['mag:viewList'] }
  },

  {
    path: '/MagasinDetail/:id',
    name: 'MagasinDetail',
    component: () => import('@/views/Stocks/Stocks.vue'),
    props: true,
    meta: { title: 'Détails du magasin', requiresPermissions: ['mag:viewDetail'] }
  },

  {
    path: '/CreateMagasin',
    name: 'CreateMagasin',
    component: () => import('@/views/Stocks/Stocks.vue'),
    meta: { title: 'Créer un magasin', requiresPermissions: ['mag:create'] }
  },

  {
    path: '/EditMagasin/:id',
    name: 'EditMagasin',
    component: () => import('@/views/Stocks/Stocks.vue'),
    props: true,
    meta: { title: 'Modifier un magasin', requiresPermissions: ['mag:edit'] }
  },

  {
    path: '/DeleteMagasin/:id',
    name: 'DeleteMagasin',
    component: () => import('@/views/Stocks/Stocks.vue'),
    props: true,
    meta: { title: 'Supprimer un magasin', requiresPermissions: ['mag:delete'] }
  },

  // Fabricants ------------------------------------------------------------------

  {
    path: '/ManufacturerList',
    name: 'ManufacturerList',
    component: () => import('@/views/DataManagement/Manufacturers/ManufacturerList.vue'),
    meta: { title: 'Fabricants', requiresPermissions: ['man:viewList'] }
  },

  {
    path: '/CreateManufacturer',
    name: 'CreateManufacturer',
    component: () => import('@/views/DataManagement/Manufacturers/CreateManufacturer.vue'),
    meta: { title: 'Creer un Fabricant', requiresPermissions: ['man:create'] }
  },

  {
    path: '/ManufacturerDetail/:id',
    name: 'ManufacturerDetail',
    component: () => import('@/views/DataManagement/Manufacturers/ManufacturerDetail.vue'),
    props: true,
    meta: { title: 'Détails d\'un fabricant', requiresPermissions: ['man:viewDetail'] }
  },
  {
    path: '/EditManufacturer/:id',
    name: 'EditManufacturer',
    component: () => import('@/views/DataManagement/Manufacturers/EditManufacturer.vue'),
    props: true,
    meta: { title: 'Modifier un Fabricant', requiresPermissions: ['man:edit'] }
  },

  // Fournisseurs ------------------------------------------------------------------

  {
    path: '/SupplierList',
    name: 'SupplierList',
    component: () => import('@/views/DataManagement/Suppliers/SupplierList.vue'),
    meta: { title: 'Fournisseurs', requiresPermissions: ['sup:viewList'] }
  },

  {
    path: '/CreateSupplier',
    name: 'CreateSupplier',
    component: () => import('@/views/DataManagement/Suppliers/CreateSupplier.vue'),
    meta: { title: 'Creer un Fournisseur', requiresPermissions: ['sup:create'] }
  },

  {
    path: '/SupplierDetail/:id',
    name: 'SupplierDetail',
    component: () => import('@/views/DataManagement/Suppliers/SupplierDetail.vue'),
    props: true,
    meta: { title: 'Détails d\'un Fournisseur', requiresPermissions: ['sup:viewDetail'] }
  },
  {
    path: '/EditSupplier/:id',
    name: 'EditSupplier',
    component: () => import('@/views/DataManagement/Suppliers/EditSupplier.vue'),
    props: true,
    meta: { title: 'Modifier un Fournisseur', requiresPermissions: ['sup:edit'] }
  },

  // GestionDonnees ---------------------------------------------------------------

  {
    path: '/DataManagement',
    name: 'DataManagement',
    component: () => import('@/views/DataManagement/DataManagement.vue'),
    // meta: { title: 'Gestion des données', requiresPermissions: ['loc:viewList'] }
    meta: { title: 'Gestion des données', requiresPermissions: ['menu:dataManagement'] }
  },

  {
    path: '/ExportData',
    name: 'ExportData',
    component: () => import('@/views/DataManagement/ExportData.vue'),
    meta: { title: 'Export de données', requiresPermissions: ['export:view'] }
  },

  // Bon de travail ---------------------------------------------------------------

  {
    path: '/InterventionList',
    name: 'InterventionList',
    component: () => import('@/views/Interventions/InterventionList.vue'),
    meta: { title: 'Bon de travail', requiresPermissions: ['bt:viewList'] }
  },

  {
    path: '/intervention/:id',
    name: 'InterventionDetail',
    component: () => import('@/views/Interventions/InterventionDetail.vue'),
    props: true,
    meta: { title: 'Détails du bon de travail', requiresPermissions: ['bt:viewDetail'] }
  },

  {
    path: '/CreateIntervention/',
    name: 'CreateIntervention',
    component: () => import('@/views/Interventions/CreateIntervention.vue'),
    meta: { title: 'Créer un bon de travail', requiresPermissions: ['bt:create'] }
  },

  {
    path: '/EditIntervention/:id',
    name: 'EditIntervention',
    component: () => import('@/views/Interventions/EditIntervention.vue'),
    props: true,
    meta: { title: 'Modifier un bon de travail', requiresPermissions: ['bt:editAll', 'bt:editAssigned'], permissionMode: 'OR' }
  },

  {
    path: '/intervention/:id/AddDocumentIntervention',
    name: 'AddDocumentIntervention',
    component: () => import('@/views/Interventions/AddDocumentIntervention.vue'),
    props: true,
    meta: { title: 'Ajouter un document au bon de travail', requiresPermissions: ['bt:editAll', 'bt:editAssigned'], permissionMode: 'OR' }
  },

  // Equipements ---------------------------------------------------------------

  {
    path: '/EquipmentList',
    name: 'EquipmentList',
    component: () => import('@/views/Equipments/EquipmentList.vue'),
    meta: { title: 'Équipements', requiresPermissions: ['eq:viewList'] }
  },

  {
    path: '/EquipmentDetail/:id',
    name: 'EquipmentDetail',
    component: () => import('@/views/Equipments/EquipmentDetail.vue'),
    props: true,
    meta: { title: 'Descriptif de l\'équipement', requiresPermissions: ['eq:viewDetail'] }
  },

  {
    path: '/CreateEquipment',
    name: 'CreateEquipment',
    component: () => import('@/views/Equipments/CreateEquipment.vue'),
    meta: { title: 'Ajouter Equipement', requiresPermissions: ['eq:create'] }
  },

  {
    path: '/EditEquipment/:id',
    name: 'EditEquipment',
    component: () => import('@/views/Equipments/EditEquipment.vue'),
    meta: { title: 'Modifier Equipement', requiresPermissions: ['eq:edit'] }
  },

  // Véhicules (flotte) ----------------------------------------------------------

  {
    path: '/VehicleList',
    name: 'VehicleList',
    component: () => import('@/views/Vehicles/VehicleList.vue'),
    meta: { title: 'Véhicules', requiresPermissions: ['veh:viewList'] }
  },

  {
    path: '/VehicleDetail/:id',
    name: 'VehicleDetail',
    component: () => import('@/views/Vehicles/VehicleDetail.vue'),
    props: true,
    meta: { title: 'Détail du véhicule', requiresPermissions: ['veh:viewDetail'] }
  },

  {
    path: '/CreateVehicle',
    name: 'CreateVehicle',
    component: () => import('@/views/Vehicles/CreateVehicle.vue'),
    meta: { title: 'Ajouter un véhicule', requiresPermissions: ['veh:create'] }
  },

  {
    path: '/EditVehicle/:id',
    name: 'EditVehicle',
    component: () => import('@/views/Vehicles/EditVehicle.vue'),
    meta: { title: 'Modifier le véhicule', requiresPermissions: ['veh:edit'] }
  },

  {
    path: '/CounterDetail/:id',
    name: 'CounterDetail',
    component: () => import('@/views/Equipments/Counters/CounterDetail.vue'),
    meta: { title: 'Détails du compteur', requiresPermissions: ['cp:viewDetail'] }
  },

  // Defaillance ---------------------------------------------------------------
  {
    path: '/FailureList',
    name: 'FailureList',
    component: () => import('@/views/Failures/FailureList.vue'),
    meta: { title: 'Demandes d\'interventions', requiresPermissions: ['di:viewList'] }
  },

  {
    path: '/CreateFailure/:equipementReference?',
    name: 'CreateFailure',
    component: () => import('@/views/Failures/CreateFailure.vue'),
    props: true,
    meta: { title: 'Demande d\'intervention', requiresPermissions: ['di:create'] }
  },

  {
    path: '/Failure/:id',
    name: 'FailureDetail',
    component: () => import('@/views/Failures/FailureDetail.vue'),
    props: true,
    meta: { title: 'Détails de la demande ', requiresPermissions: ['di:viewDetail'] }
  },

  {
    path: '/Failure/:id/edit',
    name: 'EditFailure',
    component: () => import('@/views/Failures/EditFailure.vue'),
    props: true,
    meta: { title: 'Modifier la demande d\'intervention', requiresPermissions: ['di:editCreated', 'di:editAll'], permissionMode: 'OR' }
  },

  {
    path: '/Failure/:id/addDocument',
    name: 'AddDocumentFailure',
    component: () => import('@/views/Failures/AddDocumentFailure.vue'),
    props: true,
    meta: { title: 'Ajouter un document à la demande d\'intervention', requiresPermissions: ['di:editCreated', 'di:editAll'], permissionMode: 'OR' }
  },

  // Notices ------------------------------------------------------------------
  {
    path: '/Notice',
    name: 'Notice',
    component: () => import('@/views/Notices/NoticesHome.vue'),
    meta: { title: "Notices d'utilisation", public: true }
  },

  // Lieux ---------------------------------------------------------------

  {
    path: '/LocationList',
    name: 'LocationList',
    component: () => import('@/views/DataManagement/Locations/LocationList.vue'),
    meta: { title: 'Lieux', requiresPermissions: ['loc:viewList'] }
  },

  {
    path: '/CreateLocation',
    name: 'CreateLocation',
    component: () => import('@/views/DataManagement/Locations/CreateLocation.vue'),
    meta: { title: 'Creer un lieu', requiresPermissions: ['loc:create'] }
  },

  {
    path: '/LocationDetail/:id',
    name: 'LocationDetail',
    component: () => import('@/views/DataManagement/Locations/LocationDetail.vue'),
    props: true,
    meta: { title: 'Détails d\'un lieu', requiresPermissions: ['loc:viewDetail'] }
  },

  // Modele Equipements ---------------------------------------------------------------

  {
    path: '/ModelEquipmentList',
    name: 'ModelEquipmentList',
    component: () => import('@/views/DataManagement/EquipmentsModels/ModelEquipmentList.vue'),
    meta: { title: 'Modèle', requiresPermissions: ['eqmod:viewList'] }
  },

  {
    path: '/CreateModelEquipment',
    name: 'CreateModelEquipment',
    component: () => import('@/views/DataManagement/EquipmentsModels/CreateModelEquipment.vue'),
    meta: { title: 'Creer un modele equipement', requiresPermissions: ['eqmod:create'] }
  },

  {
    path: '/ModelEquipmentDetail/:id',
    name: 'ModelEquipmentDetail',
    component: () => import('@/views/DataManagement/EquipmentsModels/ModelEquipmentDetail.vue'),
    meta: { title: 'Detail du modele equipement', requiresPermissions: ['eqmod:viewDetail'] }
  },
  {
    path: '/EditModelEquipment/:id',
    name: 'EditModelEquipment',
    component: () => import('@/views/DataManagement/EquipmentsModels/EditModelEquipment.vue'),
    meta: { title: 'Modifier modele equipement', requiresPermissions: ['eqmod:edit'] }
  },

  // Maintenance préventive -----------------------------------------------------------
  {
    path: '/MaintenancePreventive',
    name: 'PreventiveMaintenance',
    component: () => import('@/views/PreventiveMaintenance/PreventiveMaintenance.vue'),
    meta: { title: 'Maintenance préventive', requiresPermissions: ['mp:viewList'] }
  },

  // Dashboard -------------------------------------------------------------------------
  {
    path: '/Calendar',
    name: 'Calendar',
    component: () => import('@/views/Calendar/Calendar.vue'),
    meta: { title: 'Calendrier', requiresPermissions: ['menu:calendar'] }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Protection des routes
router.beforeEach((to, from, next) => {
  const userRaw = localStorage.getItem('user')
  const isAuthenticated = !!userRaw

  if (!store.getters.isAuthenticated) {
    store.dispatch('initAuth')
  }

  if (to.meta.public) {
    next()
    return
  } 

  if (!isAuthenticated) {
    next('/login')
    return
  }

  // Vérification validité auth
  if (!checkAuthValidity(store)) {
    store.commit('logout')
    next({ path: '/login', state: { message: 'Votre session a expiré. Veuillez vous reconnecter.' } })   
    return
  }

  const user = JSON.parse(userRaw)
  const userPermissions = user?.permissions_names || []

  const requiredPermissions = to.meta.requiresPermissions
  const permissionMode = to.meta.permissionMode || 'OR'

  // -----------------------------
  // Permissions
  // -----------------------------
  if (requiredPermissions && requiredPermissions.length > 0) {

    const hasPermission =
      permissionMode === 'AND'
        ? requiredPermissions.every(p => userPermissions.includes(p))
        : requiredPermissions.some(p => userPermissions.includes(p))

    if (!hasPermission) {

      // Cas spécial : self
      if (to.meta.checksIfSelf) {
        const userId = user.id
        const routeId = parseInt(to.params.id)

        if (userId === routeId) {
          next()
          return
        }
      }

      alert("Vous n'avez pas la permission d'accéder à cette page.")
      next(from.fullPath || '/')
      return
    }
  }

  next()
})

router.afterEach((to) => {
  document.title = to.meta.title ? `GIMAO - ${to.meta.title}` : 'GIMAO'
})

export default router