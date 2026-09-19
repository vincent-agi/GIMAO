<template>
  <v-dialog v-model="dialog" max-width="600px">
    <BaseForm
      v-model="formData"
      title="Transférer du stock"
      :submit-button-text="'Transférer'"
      :submit-disabled="remainingStock < 0 || transfers.length === 0"
      :handle-submit="submit"
      :custom-cancel-action="close"
      :validation-schema="validationSchema"
      :loading="loading"
    >
      <template #default>
        <v-container>
          <!-- Source Store -->
          <FormSelect
            v-model="sourceStore"
            :items="availableStores"
            item-title="title"
            item-value="magasin"
            label="Magasin Source"
            field-name="sourceStore"
            return-object
          />

          <v-divider class="my-4"></v-divider>
          <div class="text-subtitle-1 mb-2">Vers:</div>

          <!-- Destinations -->
          <div v-for="(transfer, index) in transfers" :key="index" class="transfer-row mb-2">
            <div class="transfer-destination">
              <FormSelect
                v-model="transfer.to_magasin"
                :items="allStores"
                item-title="nom"
                item-value="id"
                label="Magasin Destination"
                field-name="to_magasin"
                density="compact"
                hide-details
              />
            </div>
            <div class="transfer-quantity">
              <FormField
                v-model.number="transfer.quantite"
                label="Quantité"
                type="number"
                min="1"
                field-name="quantite"
                density="compact"
                hide-details
              />
            </div>
            <div class="transfer-delete">
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                @click="removeTransfer(index)"
              ></v-btn>
            </div>
          </div>

          <v-btn color="primary" variant="tonal" size="small" class="mt-2" @click="addTransfer">
            + Ajouter destination
          </v-btn>

          <v-alert v-if="remainingStock < 0" type="error" density="compact" class="mt-4">
            Stock insuffisant (Manque: {{ Math.abs(remainingStock) }})
          </v-alert>
          <v-alert v-else-if="sourceStore?.magasin_nom" type="info" density="compact" class="mt-4">
            Reste en stock dans {{ sourceStore.magasin_nom }} après transfert : {{ remainingStock }}
          </v-alert>
        </v-container>
      </template>
    </BaseForm>
  </v-dialog>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import { BaseForm, FormField, FormSelect } from '@/components/common'

  const props = defineProps({
    modelValue: Boolean,
    consumable: { type: Object, default: null },
  })

  const emit = defineEmits(['update:modelValue', 'transfer-complete'])
  const api = useApi(API_BASE_URL)

  const dialog = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val),
  })

  const formData = ref({
    sourceStore: null,
  })
  const loading = ref(false)
  const sourceStore = computed({
    get: () => formData.value.sourceStore,
    set: (value) => {
      formData.value.sourceStore = value
    },
  })
  const transfers = ref([{ to_magasin: null, quantite: 1 }])
  const allStores = ref([])
  const loadingStores = ref(false)

  const validationSchema = {
    sourceStore: ['required'],
  }

  // Stores that have stock
  const availableStores = computed(() => {
    if (!props.consumable?.stocks) return []
    return props.consumable.stocks
      .filter((s) => s.quantite > 0)
      .map((s) => ({ ...s, title: `${s.magasin_nom} (Stock: ${s.quantite})` }))
  })

  const remainingStock = computed(() => {
    if (!sourceStore.value) return 0
    const totalTransfer = transfers.value
      .filter((t) => t.to_magasin)
      .reduce((sum, t) => sum + (parseInt(t.quantite) || 0), 0)
    return sourceStore.value.quantite - totalTransfer
  })

  const fetchAllStores = async () => {
    loadingStores.value = true
    try {
      const response = await api.get('magasins/')
      allStores.value = response.results || response
    } catch (e) {
      console.error('Error fetching stores', e)
    } finally {
      loadingStores.value = false
    }
  }

  const addTransfer = () => {
    transfers.value.push({ to_magasin: null, quantite: 1 })
  }

  const removeTransfer = (index) => {
    transfers.value.splice(index, 1)
  }

  const close = () => {
    dialog.value = false
    formData.value.sourceStore = null
    transfers.value = [{ to_magasin: null, quantite: 1 }]
  }

  const submit = async () => {
    // BaseForm sets loading automatically if handleSubmit returns promise? No, BaseForm prop 'loading' controls button state usually.
    // Actually BaseForm calls handleSubmit(formData)
    // BaseForm's handleSubmit:
    /*
  if (props.handleSubmit && typeof props.handleSubmit === 'function') {
    try {
      await props.handleSubmit(formData.value);
    } ...
  }
  */
    // So I don't need to manually set loading if I pass `loading` prop but BaseForm doesn't auto-set it based on promise.
    // I will keep manual loading management or I can let BaseForm handle errors if I throw?
    // I'll keep my manual loading for now to be safe with existing logic.

    const selectedTransfers = transfers.value.filter((t) => t.to_magasin)
    const hasInvalidTransfer = selectedTransfers.some((t) => !t.quantite || Number(t.quantite) < 1)
    if (selectedTransfers.length === 0) {
      throw new Error('Veuillez sélectionner au moins un magasin destination.')
    }
    if (!sourceStore.value || remainingStock.value < 0 || hasInvalidTransfer) return
    loading.value = true
    try {
      const payload = {
        from_magasin: sourceStore.value.magasin, // stock object has magasin ID in 'magasin' field
        transfers: selectedTransfers,
      }
      await api.post(`consommables/${props.consumable.id}/transfer_stock/`, payload)
      emit('transfer-complete')
      close()
    } catch (error) {
      console.error('Transfer failed', error)
      // Re-throw to show error in BaseForm? BaseForm catches errors from handleSubmit.
      throw error
    } finally {
      loading.value = false
    }
  }

  onMounted(fetchAllStores)
</script>

<style scoped>
  .transfer-row {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    flex-wrap: nowrap;
  }

  .transfer-destination {
    flex: 1 1 auto;
    min-width: 0;
  }

  .transfer-quantity {
    flex: 0 0 120px;
  }

  .transfer-delete {
    flex: 0 0 auto;
    width: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding-bottom: 4px;
  }
</style>
