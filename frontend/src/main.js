import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import VueApexCharts from 'vue3-apexcharts'
import './assets/css/global.css'
import '@mdi/font/css/materialdesignicons.css'
import { initializeTheme } from './utils/theme'

const app = createApp(App)

// Add favicon dynamically
const link = document.createElement('link')
link.setAttribute('rel', 'icon')
link.setAttribute('type', 'image/png')
link.setAttribute('href', require('@/assets/favicon.png'))
document.head.appendChild(link)

// Utilisez le store Vuex
app.use(store)

// Utilisez le routeur
app.use(router)

// Utilisez Vuetify
app.use(vuetify)

// ApexCharts (graphiques)
app.use(VueApexCharts)

// Applique le thème sauvegardé au démarrage
initializeTheme()

// Montez l'application
app.mount('#app')
