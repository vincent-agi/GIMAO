import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import eslintConfigPrettier from 'eslint-config-prettier'

export default [
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        process: 'readonly',
        localStorage: 'readonly',
        fetch: 'readonly',
        // require() fonctionne à l'exécution via le bundler webpack (vue-cli).
        require: 'readonly',
      },
    },
    rules: {
      // Composants a nom unique tolérés (ex. App.vue, Home.vue)
      'vue/multi-word-component-names': 'off',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  },
  {
    files: ['**/__tests__/**/*.js', '**/*.test.js', '**/*.spec.js'],
    languageOptions: {
      globals: {
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        vi: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        global: 'writable',
      },
    },
  },
  {
    files: ['vue.config.js', 'babel.config.js'],
    languageOptions: {
      sourceType: 'commonjs',
      globals: {
        require: 'readonly',
        module: 'writable',
        process: 'readonly',
      },
    },
  },
  {
    // Config Vite : ESM, mais __dirname reste injecté par le loader vite-node.
    files: ['vitest.config.js'],
    languageOptions: {
      globals: {
        __dirname: 'readonly',
      },
    },
  },
  {
    // modelValue muté directement (objet partagé par référence avec le parent,
    // via v-model="formData" dans CreateEquipment/EditEquipment). Fonctionne car
    // la réactivité Vue suit la même référence ; passer à un emit par champ est
    // un refactor à risque sur un formulaire multi-étapes, non fait ici.
    files: ['src/components/Forms/EquipmentFormFields.vue'],
    rules: {
      'vue/no-mutating-props': 'off',
    },
  },
  {
    ignores: ['dist/**', 'node_modules/**', 'coverage/**', 'public/**'],
  },
  eslintConfigPrettier,
]
