/**
 * Plugin Vue pour enregistrer globalement les composants de formulaire
 *
 * Usage dans main.js:
 * import formComponents from '@/components/common/plugin';
 * app.use(formComponents);
 *
 * Après, vous pouvez utiliser les composants sans import:
 * <BaseForm ... />
 * <FormAlert ... />
 * etc.
 */

import BaseForm from './BaseForm.vue'
import FormAlert from './FormAlert.vue'
import FormActions from './FormActions.vue'
import FormContainer from './FormContainer.vue'
import BaseListView from './BaseListView.vue'
import BaseDetailView from './BaseDetailView.vue'
import {
  FormField,
  FormSelect,
  FormFileInput,
  FormTextarea,
  FormCheckbox,
  FormRadio,
  FormDatePicker,
} from '../Forms/inputType'

export default {
  install(app) {
    // Enregistrement global des composants
    app.component('BaseForm', BaseForm)
    app.component('FormAlert', FormAlert)
    app.component('FormActions', FormActions)
    app.component('FormContainer', FormContainer)
    app.component('BaseListView', BaseListView)
    app.component('BaseDetailView', BaseDetailView)
    app.component('FormField', FormField)
    app.component('FormSelect', FormSelect)
    app.component('FormFileInput', FormFileInput)
    app.component('FormTextarea', FormTextarea)
    app.component('FormCheckbox', FormCheckbox)
    app.component('FormRadio', FormRadio)
    app.component('FormDatePicker', FormDatePicker)
  },
}

/**
 * Alternative: Import nommés pour usage local
 *
 * import { BaseForm, FormAlert, FormActions, FormContainer } from '@/components/common';
 */
export { BaseForm, FormAlert, FormActions, FormContainer }
