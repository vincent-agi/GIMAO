import { render, screen } from '@testing-library/vue'
import { describe, it, expect } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createStore } from 'vuex'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import SideBar from '../SideBar.vue'

const SideBarInApp = {
  components: { SideBar },
  template: '<v-app><SideBar /></v-app>',
}

const vuetify = createVuetify({ components, directives })

const NAV_ROUTE_NAMES = [
  'Dashboard',
  'EquipmentList',
  'VehicleList',
  'FailureList',
  'InterventionList',
  'PreventiveMaintenance',
  'Calendar',
  'UserList',
  'Stocks',
  'DataManagement',
]

const makeRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: NAV_ROUTE_NAMES.map((name) => ({
      path: `/${name}`,
      name,
      component: { render: () => null },
    })),
  })

const renderSideBar = (permissions = []) => {
  const store = createStore({
    getters: {
      hasPermission: () => (perm) => permissions.includes(perm),
      currentUser: () => ({ prenom: 'Jean', nomFamille: 'Dupont', role: { nomRole: 'Test' } }),
    },
  })
  const router = makeRouter()
  return render(SideBarInApp, { global: { plugins: [vuetify, store, router] } })
}

describe('SideBar.vue — entrée de menu Véhicules', () => {
  it('affiche le lien Véhicules quand veh:viewList est accordé', async () => {
    renderSideBar(['veh:viewList'])

    expect(await screen.findByText('Véhicules')).toBeDefined()
  })

  it("n'affiche pas le lien Véhicules sans la permission veh:viewList", async () => {
    renderSideBar([])

    expect(screen.queryByText('Véhicules')).toBeNull()
  })
})
