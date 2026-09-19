import vuetify, { THEME_STORAGE_KEY } from '@/plugins/vuetify'

const normalizeThemeName = (themeName) => (themeName === 'dark' ? 'dark' : 'light')

const persistAndReflectTheme = (themeName) => {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.setItem(THEME_STORAGE_KEY, themeName)
  document.documentElement.setAttribute('data-theme', themeName)
}

export const applyTheme = (themeName) => {
  const normalizedTheme = normalizeThemeName(themeName)
  vuetify.theme.global.name.value = normalizedTheme
  persistAndReflectTheme(normalizedTheme)
  return normalizedTheme
}

export const initializeTheme = () => {
  if (typeof window === 'undefined') {
    return 'light'
  }

  const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY)
  return applyTheme(savedTheme)
}

export const toggleTheme = () => {
  const nextTheme = vuetify.theme.global.current.value.dark ? 'light' : 'dark'
  return applyTheme(nextTheme)
}
