<template>
  <BaseForm
    title="Modifier le compteur"
    :loading="loading"
    @submit="handleSubmit"
    @cancel="handleCancel"
  >
    <v-container fluid>
      <v-row dense>
        <v-col cols="12">
          <v-text-field
            v-model="form.nomCompteur"
            label="Nom"
            variant="outlined"
            density="compact"
            :rules="[rules.required]"
          />
        </v-col>
      </v-row>

      <v-row dense>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="form.unite"
            label="Unité"
            variant="outlined"
            density="compact"
            :rules="[rules.required]"
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            v-model.number="form.valeurCourante"
            label="Valeur courante"
            variant="outlined"
            density="compact"
            type="number"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-2">
        <v-col cols="12" md="4">
          <v-switch
            v-model="form.estPrincipal"
            label="Compteur principal"
            color="primary"
            hide-details
          />
        </v-col>
      </v-row>
    </v-container>
  </BaseForm>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { useApi } from '@/composables/useApi'
  import { useStore } from 'vuex'
  import { API_BASE_URL } from '@/utils/constants'
  import BaseForm from '@/components/common/BaseForm.vue'

  const props = defineProps({
    counter: {
      type: Object,
      default: () => ({}),
    },
    isCounterEdit: {
      type: Boolean,
      default: false,
    },
  })

  const emit = defineEmits(['submit', 'cancel'])

  const loading = ref(false)

  const api = useApi(API_BASE_URL)
  const store = useStore()

  const form = ref({
    nomCompteur: '',
    unite: '',
    valeurCourante: null,
    estPrincipal: false,
  })

  const rules = {
    required: (v) => !!v || 'Ce champ est requis',
  }

  onMounted(() => {
    if (props.counter) {
      form.value = {
        nomCompteur: props.counter.nomCompteur || '',
        unite: props.counter.unite || '',
        valeurCourante: props.counter.valeurCourante ?? null,
        estPrincipal: props.counter.estPrincipal || false,
      }
    }
  })

  const handleSubmit = async () => {
    if (props.isCounterEdit) {
      const changes = detectChanges()

      changes.user = store.getters.currentUser.id

      try {
        api.put(`compteurs/${props.counter.id}/`, changes)

        emit('submit', { ...form.value })
      } catch (error) {
        console.error('Erreur lors de la détection des changements :', error)
      }
    } else {
      try {
        await api.post('compteurs/', { ...form.value })

        emit('submit', { ...form.value })
      } catch (error) {
        console.error('Erreur lors de la création du compteur :', error)
      }

      emit('submit', { ...form.value })
    }
  }

  const detectChanges = () => {
    const changes = {}
    if (form.value.nomCompteur !== props.counter.nomCompteur) {
      changes.nomCompteur = {
        ancienne: props.counter.nomCompteur,
        nouvelle: form.value.nomCompteur,
      }
    }
    if (form.value.unite !== props.counter.unite) {
      changes.unite = {
        ancienne: props.counter.unite,
        nouvelle: form.value.unite,
      }
    }
    if (form.value.valeurCourante !== props.counter.valeurCourante) {
      changes.valeurCourante = {
        ancienne: props.counter.valeurCourante,
        nouvelle: form.value.valeurCourante,
      }
    }
    if (form.value.estPrincipal !== props.counter.estPrincipal) {
      changes.estPrincipal = {
        ancienne: props.counter.estPrincipal,
        nouvelle: form.value.estPrincipal,
      }
    }
    return changes
  }

  const handleCancel = () => {
    emit('cancel')
  }
</script>
