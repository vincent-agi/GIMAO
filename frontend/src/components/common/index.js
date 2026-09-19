/**
 * Export centralisé des composants de formulaire
 *
 * Usage local (recommandé):
 * import { FormAlert, FormActions, FormContainer } from '@/components/common';
 *
 * Usage global (via plugin):
 * import formComponents from '@/components/common/plugin';
 * app.use(formComponents);
 */

// Export des composants individuels
export { default as FormAlert } from './FormAlert.vue'
export { default as FormActions } from './FormActions.vue'
export { default as FormContainer } from './FormContainer.vue'

// Ré-exporter tous les composants de saisie depuis inputType
export {
  FormField,
  FormSelect,
  FormFileInput,
  FormTextarea,
  FormCheckbox,
  FormRadio,
  FormDatePicker,
} from '../Forms/inputType'

// Export des composants principaux
export { default as BaseForm } from './BaseForm.vue'
export { default as BaseListView } from './BaseListView.vue'
export { default as BaseDetailView } from './BaseDetailView.vue'
export { default as ServerPaginationControls } from './ServerPaginationControls.vue'
export { default as FloatingCreateButton } from './FloatingCreateButton.vue'

// Export du plugin Vue (pour enregistrement global)
export { default as formComponentsPlugin } from './plugin.js'
