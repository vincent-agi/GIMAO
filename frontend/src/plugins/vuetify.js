import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

export const THEME_STORAGE_KEY = 'gimao-theme'

const getDefaultTheme = () => {
  if (typeof window === 'undefined') {
    return 'light'
  }

  return window.localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light'
}

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: getDefaultTheme(),
    themes: {
      light: {
        dark: false,
        colors: {
          background: '#f6f8fc',
          surface: '#ffffff',
          primary: '#5d5fef',
          secondary: '#05004E',
          error: '#ef4444',
          info: '#3b82f6',
          success: '#10b981',
          warning: '#f59e0b',
        },
      },
      dark: {
        dark: true,
        colors: {
          background: '#101522',
          surface: '#1b2435',
          primary: '#8f91ff',
          secondary: '#c7d2fe',
          error: '#f87171',
          info: '#60a5fa',
          success: '#34d399',
          warning: '#fbbf24',
        },
      },
    },
  },
})

export default vuetify
