<template>
  <v-app>
    <v-main>
      <v-container fluid>
        <v-row>
          <v-col cols="12">
            <h1 class="text-h3 font-weight-bold text-primary mb-6 text-center">
              Gestion des Données
            </h1>
          </v-col>
        </v-row>
        <v-row justify="center">
          <v-col v-for="menu_item in filtered_menu_items" :key="menu_item.name" cols="12" sm="6">
            <v-card
              elevation="2"
              class="rounded-lg pa-4 mb-4 data_card"
              @click="navigate_to(menu_item.route)"
            >
              <v-card-text class="text-center">
                <v-icon :color="menu_item.color" size="64" class="mb-4">{{
                  menu_item.icon
                }}</v-icon>
                <h2 class="text-h5 font-weight-medium">{{ menu_item.name }}</h2>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
  export default {
    name: 'DataManagement',
    data() {
      return {
        menu_items: [
          {
            name: 'Lieux',
            route: '/LocationList',
            icon: 'mdi-map-marker',
            color: 'blue',
            requiresPermission: 'loc:viewList',
          },
          {
            name: 'Fournisseurs',
            route: '/SupplierList',
            icon: 'mdi-truck',
            color: 'orange',
            requiresPermission: 'sup:viewList',
          },
          {
            name: 'Fabricants',
            route: '/ManufacturerList',
            icon: 'mdi-factory',
            color: 'red',
            requiresPermission: 'man:viewList',
          },
          {
            name: "Modèles d'équipements",
            route: '/ModelEquipmentList',
            icon: 'mdi-cog',
            color: 'purple',
            requiresPermission: 'eqmod:viewList',
          },
          {
            name: 'Rôles',
            route: '/RoleList',
            icon: 'mdi-shield-account',
            color: 'green',
            requiresPermission: 'role:viewList',
          },
          {
            name: 'Export de données',
            route: '/ExportData',
            icon: 'mdi-database-export',
            color: 'teal',
            requiresPermission: 'export:view',
          },
        ],
      }
    },
    computed: {
      filtered_menu_items() {
        return this.menu_items.filter((item) => {
          return this.$store.getters.hasPermission(item.requiresPermission)
        })
      },
    },
    methods: {
      navigate_to(route) {
        this.$router.push(route)
      },
    },
  }
</script>

<style scoped>
  .text-primary {
    color: #05004e;
  }

  .data_card {
    transition:
      transform 0.3s,
      box-shadow 0.3s;
    cursor: pointer;
  }

  .data_card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
  }

  .v-icon {
    transition: transform 0.3s;
  }

  .data_card:hover .v-icon {
    transform: scale(1.1);
  }
</style>
