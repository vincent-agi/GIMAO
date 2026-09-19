<template>
  <v-dialog v-model="dialog" max-width="800px">
    <BaseForm
      v-model="purchase"
      title="Ajouter un achat"
      :show-actions="false"
      :custom-cancel-action="close"
      :validation-schema="validationSchema"
    >
      <template #default="{ validation }">
        <v-stepper
          v-model="step"
          :items="['Informations', 'Distribution']"
          class="elevation-0"
          :hide-actions="true"
        >
          <template #[`item.1`]>
            <v-card flat>
              <v-container>
                <v-alert v-if="stepOneError" type="error" density="compact" class="mb-4">
                  {{ stepOneError }}
                </v-alert>
                <v-row>
                  <!-- Date -->
                  <v-col cols="12" sm="6">
                    <FormField
                      v-model="purchase.date_reference_prix"
                      label="Date"
                      type="date"
                      field-name="date_reference_prix"
                      :step="1"
                    />
                  </v-col>

                  <!-- Quantité -->
                  <v-col cols="12" sm="6">
                    <FormField
                      v-model.number="purchase.quantite"
                      label="Quantité Achetée"
                      type="number"
                      min="1"
                      field-name="quantite"
                      :step="1"
                    />
                  </v-col>

                  <!-- Prix Unitaire -->
                  <v-col cols="12" sm="6">
                    <FormField
                      v-model.number="purchase.prix_unitaire"
                      label="Prix Unitaire (€)"
                      type="number"
                      min="0"
                      field-name="prix_unitaire"
                      :step="1"
                    />
                  </v-col>

                  <!-- Fournisseur -->
                  <v-col cols="12">
                    <FormSelect
                      v-model="purchase.fournisseur"
                      :items="suppliers"
                      item-title="nom"
                      item-value="id"
                      label="Fournisseur *"
                      field-name="fournisseur"
                      :step="1"
                      :loading="loadingSuppliers"
                    />
                  </v-col>

                  <!-- Fabricant -->
                  <v-col cols="12">
                    <FormSelect
                      v-model="purchase.fabricant"
                      :items="manufacturers"
                      item-title="nom"
                      item-value="id"
                      label="Fabricant *"
                      field-name="fabricant"
                      :step="1"
                      :loading="loadingManufacturers"
                    />
                  </v-col>
                </v-row>
              </v-container>
            </v-card>
          </template>

          <template #[`item.2`]>
            <v-card flat>
              <v-card-text>
                <div class="d-flex justify-space-between mb-4">
                  <strong>Total Acheté: {{ purchase.quantite }}</strong>
                  <strong>Distribué: {{ totalDistributed }}</strong>
                  <strong :class="remainingToDistribute === 0 ? 'text-success' : 'text-error'">
                    Reste: {{ remainingToDistribute }}
                  </strong>
                </div>

                <v-alert
                  v-if="distributionList.length === 0"
                  type="info"
                  density="compact"
                  class="mt-4"
                >
                  Aucun magasin disponible. Ajoutez un magasin pour finaliser la distribution.
                </v-alert>

                <v-table v-else density="compact">
                  <thead>
                    <tr>
                      <th>Magasin</th>
                      <th class="text-right" style="width: 180px">Quantité</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="store in distributionList" :key="store.id">
                      <td>{{ store.nom }}</td>
                      <td>
                        <FormField
                          v-model.number="store.quantite"
                          type="number"
                          min="0"
                          field-name="quantite_distribution"
                          hide-details
                          density="compact"
                        />
                      </td>
                    </tr>
                  </tbody>
                </v-table>
                <v-alert
                  v-if="distributionList.length > 0 && remainingToDistribute !== 0"
                  type="warning"
                  density="compact"
                  class="mt-4"
                >
                  Vous devez distribuer exactement la quantité achetée.
                </v-alert>

                <div class="d-flex justify-end mt-3">
                  <v-btn color="primary" variant="outlined" size="small" @click="openMagasinForm">
                    Ajouter un magasin
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </template>
        </v-stepper>

        <div class="d-flex justify-end pa-4">
          <v-btn v-if="step > 1" variant="text" @click="step--">Précédent</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="blue-darken-1" variant="text" @click="close">Annuler</v-btn>
          <v-btn v-if="step < 2" color="primary" class="ml-2" @click="nextStep(validation)">
            Suivant
          </v-btn>
          <v-btn
            v-else
            color="primary"
            :disabled="remainingToDistribute !== 0 || loading"
            :loading="loading"
            class="ml-2"
            @click="save"
          >
            Confirmer Achat
          </v-btn>
        </div>
      </template>
    </BaseForm>

    <v-dialog v-model="showMagasinFormDialog" max-width="500px">
      <v-card class="rounded-lg">
        <MagasinForm
          :magasin="magasinToEdit"
          @created="handleMagasinCreated"
          @updated="handleMagasinCreated"
          @close="showMagasinFormDialog = false"
        />
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import { BaseForm, FormField, FormSelect } from '@/components/common'
  import MagasinForm from '@/components/Forms/MagasinForm.vue'

  const props = defineProps({
    modelValue: Boolean,
    consumableId: {
      type: [Number, String],
      required: true,
    },
  })
  // ... (rest of script as before, minimal changes needed except imports)
  const emit = defineEmits(['update:modelValue', 'purchase-added'])
  const api = useApi(API_BASE_URL)
  const dialog = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val),
  })

  const step = ref(1)
  const loading = ref(false)
  const stepOneError = ref('')
  const showMagasinFormDialog = ref(false)
  const magasinToEdit = ref(null)
  // ... (data refs same as before)
  // Data for selects
  const suppliers = ref([])
  const manufacturers = ref([])
  const stores = ref([])
  const loadingSuppliers = ref(false)
  const loadingManufacturers = ref(false)

  const purchase = ref({
    date_reference_prix: new Date().toISOString().substr(0, 10),
    quantite: 1,
    prix_unitaire: 0,
    fournisseur: null,
    fabricant: null,
  })
  const distributionList = ref([])

  const validationSchema = {
    step1: {
      date_reference_prix: ['required'],
      quantite: ['required', 'numeric', 'positive'],
      prix_unitaire: ['required', 'numeric', { name: 'min', params: [0] }],
      fournisseur: ['required'],
      fabricant: ['required'],
    },
  }

  const totalDistributed = computed(() => {
    return distributionList.value.reduce((sum, s) => sum + (parseInt(s.quantite) || 0), 0)
  })

  const remainingToDistribute = computed(() => {
    return (parseInt(purchase.value.quantite) || 0) - totalDistributed.value
  })

  // Fetch functions same as before
  const fetchSuppliers = async () => {
    loadingSuppliers.value = true
    try {
      const response = await api.get('fournisseurs/')
      suppliers.value = response.results || response
    } catch (e) {
      console.error('Error fetching suppliers', e)
    } finally {
      loadingSuppliers.value = false
    }
  }
  const fetchManufacturers = async () => {
    loadingManufacturers.value = true
    try {
      const response = await api.get('fabricants/')
      manufacturers.value = response.results || response
    } catch (e) {
      console.error('Error fetching manufacturers', e)
    } finally {
      loadingManufacturers.value = false
    }
  }
  const fetchStores = async () => {
    try {
      const response = await api.get('magasins/')
      stores.value = response.results || response
      distributionList.value = stores.value.map((s) => ({
        id: s.id,
        nom: s.nom,
        quantite: 0,
      }))
    } catch (e) {
      console.error('Error fetching stores', e)
    }
  }

  onMounted(() => {
    fetchSuppliers()
    fetchManufacturers()
    fetchStores()
  })

  const nextStep = (validation) => {
    if (step.value !== 1) return

    if (!purchase.value.fournisseur || !purchase.value.fabricant) {
      stepOneError.value = 'Le fournisseur et le fabricant sont obligatoires.'
      return
    }

    if (validation?.validateStep(1, purchase.value)) {
      stepOneError.value = ''
      step.value = 2
      return
    }

    stepOneError.value = 'Veuillez corriger les champs obligatoires avant de continuer.'
  }

  const openMagasinForm = () => {
    magasinToEdit.value = null
    showMagasinFormDialog.value = true
  }

  const handleMagasinCreated = async () => {
    showMagasinFormDialog.value = false
    await fetchStores()
  }

  const close = () => {
    dialog.value = false
    step.value = 1
    stepOneError.value = ''
  }

  const save = async () => {
    if (remainingToDistribute.value !== 0) return
    loading.value = true
    try {
      const payload = {
        consommable: props.consumableId,
        fournisseur: purchase.value.fournisseur,
        fabricant: purchase.value.fabricant,
        quantite: purchase.value.quantite,
        prix_unitaire: purchase.value.prix_unitaire,
        date_reference_prix: purchase.value.date_reference_prix,
        distribution: distributionList.value
          .filter((s) => s.quantite > 0)
          .map((s) => ({ magasin: s.id, quantite: s.quantite })),
      }
      await api.post('fournitures/', payload)
      emit('purchase-added')
      close()
      step.value = 1
      purchase.value = {
        date_reference_prix: new Date().toISOString().substr(0, 10),
        quantite: 1,
        prix_unitaire: 0,
        fournisseur: null,
        fabricant: null,
      }
      distributionList.value.forEach((s) => {
        s.quantite = 0
      })
    } catch (error) {
      console.error('Error saving purchase', error)
    } finally {
      loading.value = false
    }
  }
</script>
