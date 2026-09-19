<template>
  <v-row>
    <template v-if="showGeneral">
      <!-- Informations générales -->
      <v-col cols="12">
        <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
          Informations générales
        </v-card-subtitle>
      </v-col>

      <v-col cols="12" md="6">
        <FormField
          v-model="modelValue.numSerie"
          field-name="numSerie"
          :step="step"
          label="Numéro de série"
          placeholder="Saisir le numéro de série"
          counter="100"
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormField
          v-model="modelValue.reference"
          field-name="reference"
          :step="step"
          label="Code GMAO"
          placeholder="Saisir le code GMAO"
          counter="100"
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormField
          v-model="modelValue.designation"
          field-name="designation"
          :step="step"
          label="Désignation"
          placeholder="Saisir la désignation"
          counter="100"
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormSelect
          v-model="modelValue.type"
          field-name="type"
          :step="step"
          label="Type d'équipement"
          placeholder="Sélectionner un type"
          :items="EQUIPMENT_TYPES"
          item-title="title"
          item-value="value"
          clearable
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormField
          v-model="modelValue.dateMiseEnService"
          field-name="dateMiseEnService"
          :step="step"
          label="Date de mise en service"
          type="date"
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormField
          v-model="modelValue.prixAchat"
          field-name="prixAchat"
          :step="step"
          label="Prix d'achat"
          placeholder="0.00"
          suffix="€"
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormFileInput
          label="Image de l'équipement"
          placeholder="Sélectionner une image"
          accept="image/*"
          prepend-inner-icon="mdi-camera"
          :default-preview-image="lienImageEquipement"
          @update:model-value="handleFileUpload"
        />
      </v-col>

      <v-col v-if="showStatus" cols="12" md="6" class="mt-2">
        <FormSelect
          v-model="modelValue.statut"
          field-name="statut"
          :step="step"
          label="Statut"
          :items="equipmentStatuses"
          item-title="label"
          item-value="value"
        />
      </v-col>
    </template>

    <template v-if="showModelInfo">
      <v-col cols="12">
        <v-divider class="my-4"></v-divider>
        <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
          Modèle et références
        </v-card-subtitle>
      </v-col>

      <v-col cols="12" md="6">
        <FormSelect
          v-model="modelValue.modeleEquipement"
          field-name="modeleEquipement"
          :step="step"
          label="Modèle"
          :items="equipmentModels"
          item-title="nom"
          item-value="id"
          clearable
          no-filter
          :loading="equipmentModelsLoading"
          @update:search="$emit('search-equipment-models', $event)"
        >
          <template #append-item>
            <v-divider class="mt-2" />
            <v-list-item @click="$emit('open-modele-dialog')">
              <template #prepend>
                <v-icon color="primary">mdi-plus</v-icon>
              </template>
              <v-list-item-title>Créer un nouveau modèle</v-list-item-title>
            </v-list-item>
          </template>
        </FormSelect>
      </v-col>

      <v-col cols="12" md="6">
        <FormSelect
          v-model="modelValue.fournisseur"
          field-name="fournisseur"
          :step="step"
          label="Fournisseur"
          :items="fournisseurs"
          item-title="nom"
          item-value="id"
          clearable
          no-filter
          :loading="fournisseursLoading"
          @update:search="$emit('search-fournisseurs', $event)"
        >
          <template #append-item>
            <v-divider class="mt-2" />
            <v-list-item @click="$emit('open-fournisseur-dialog')">
              <template #prepend>
                <v-icon color="primary">mdi-plus</v-icon>
              </template>
              <v-list-item-title>Créer un nouveau fournisseur</v-list-item-title>
            </v-list-item>
          </template>
        </FormSelect>
      </v-col>

      <v-col cols="12" md="6">
        <FormSelect
          v-model="modelValue.fabricant"
          field-name="fabricant"
          :step="step"
          label="Fabricant"
          :items="fabricants"
          item-title="nom"
          item-value="id"
          clearable
          no-filter
          :loading="fabricantsLoading"
          @update:search="$emit('search-fabricants', $event)"
        >
          <template #append-item>
            <v-divider class="mt-2" />
            <v-list-item @click="$emit('open-fabricant-dialog')">
              <template #prepend>
                <v-icon color="primary">mdi-plus</v-icon>
              </template>
              <v-list-item-title>Créer un nouveau fabricant</v-list-item-title>
            </v-list-item>
          </template>
        </FormSelect>
      </v-col>

      <v-col cols="12" md="6">
        <FormSelect
          v-model="modelValue.famille"
          field-name="famille"
          :step="step"
          label="Famille"
          :items="familles"
          item-title="nom"
          item-value="id"
          clearable
        >
          <template #append-item>
            <v-divider class="mt-2" />
            <v-list-item @click="$emit('open-famille-dialog')">
              <template #prepend>
                <v-icon color="primary">mdi-plus</v-icon>
              </template>
              <v-list-item-title>Créer une nouvelle famille</v-list-item-title>
            </v-list-item>
          </template>
        </FormSelect>
      </v-col>
    </template>

    <!-- Localisation et Statut -->
    <template v-if="showLocation">
      <v-col cols="12">
        <v-divider class="my-4"></v-divider>
        <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
          Localisation et statut
        </v-card-subtitle>
      </v-col>

      <v-col v-if="showLocation" cols="12" :md="showStatus ? 6 : 12">
        <LocationTreeView
          v-model:selected="modelValue.lieu"
          :items="locations"
          :show-create-button="true"
          @create="$emit('open-lieu-dialog', $event)"
          @created="handleLocationCreated"
        />
      </v-col>
    </template>

    <!-- Consommables -->
    <template v-if="showConsommables">
      <v-col cols="12">
        <v-divider class="my-4"></v-divider>
        <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
          Consommables associés
        </v-card-subtitle>
      </v-col>

      <v-col cols="12">
        <FormSelect
          v-model="modelValue.consommables"
          label="Consommables"
          :items="consumables"
          item-title="designation"
          item-value="id"
          multiple
          chips
          clearable
          no-filter
          :loading="consumablesLoading"
          @update:search="$emit('search-consumables', $event)"
        >
          <template #append-item>
            <v-divider class="mt-2" />
            <v-list-item @click="$emit('open-consommable-dialog')">
              <template #prepend>
                <v-icon color="primary">mdi-plus</v-icon>
              </template>
              <v-list-item-title>Ajouter un consommable</v-list-item-title>
            </v-list-item>
          </template>
        </FormSelect>
      </v-col>
    </template>

    <!-- Compteurs -->
    <template v-if="showCounters">
      <v-col cols="12">
        <v-divider class="my-4"></v-divider>
        <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2"> Compteurs </v-card-subtitle>
      </v-col>

      <v-col cols="12">
        <v-data-table
          :items="modelValue.compteurs"
          :headers="TABLE_HEADERS.COUNTERS"
          class="elevation-1"
          density="comfortable"
        >
          <template #[`item.nom`]="{ item }">
            {{ item.nom }}
          </template>
          <template #[`item.intervalle`]="{ item }">
            {{ item.intervalle }}
          </template>
          <template #[`item.unite`]="{ item }">
            {{ item.unite }}
          </template>
          <template #[`item.options`]="{ item }">
            <div>
              {{ item.estPrincipal ? ' Principal' : ' Aucune' }}
            </div>
          </template>
          <template #[`item.planMaintenance`]="{ item }">
            <div class="d-flex align-center">
              <v-icon size="small" class="mr-1">mdi-wrench</v-icon>
              <span class="text-truncate" style="max-width: 200px">
                {{ item.planMaintenance?.nom || 'Aucun plan associé' }}
              </span>
            </div>
          </template>
          <template #[`item.actions`]="{ item }">
            <div class="d-flex gap-1">
              <v-btn
                icon="mdi-pencil"
                size="small"
                color="primary"
                variant="text"
                @click="$emit('edit-counter', item)"
              />
              <v-btn
                icon="mdi-delete"
                size="small"
                color="error"
                variant="text"
                @click="$emit('delete-counter', item)"
              />
            </div>
          </template>
        </v-data-table>
      </v-col>
    </template>
  </v-row>
</template>

<script setup>
  import { FormField, FormSelect, FormFileInput } from '@/components/common'
  import LocationTreeView from '@/components/LocationTreeView.vue'
  import { TABLE_HEADERS, EQUIPMENT_TYPES } from '@/utils/constants'

  defineProps({
    modelValue: {
      type: Object,
      required: true,
    },
    equipmentModels: {
      type: Array,
      default: () => [],
    },
    fournisseurs: {
      type: Array,
      default: () => [],
    },
    fabricants: {
      type: Array,
      default: () => [],
    },
    familles: {
      type: Array,
      default: () => [],
    },
    locations: {
      type: Array,
      default: () => [],
    },
    consumables: {
      type: Array,
      default: () => [],
    },
    equipmentModelsLoading: {
      type: Boolean,
      default: false,
    },
    fournisseursLoading: {
      type: Boolean,
      default: false,
    },
    fabricantsLoading: {
      type: Boolean,
      default: false,
    },
    consumablesLoading: {
      type: Boolean,
      default: false,
    },
    equipmentStatuses: {
      type: Array,
      default: () => [],
    },
    lienImageEquipement: {
      type: String,
      default: '',
    },
    step: {
      type: Number,
      default: undefined,
    },
    showLocation: {
      type: Boolean,
      default: true,
    },
    showStatus: {
      type: Boolean,
      default: true,
    },
    showConsommables: {
      type: Boolean,
      default: true,
    },
    showCounters: {
      type: Boolean,
      default: true,
    },
    showGeneral: {
      type: Boolean,
      default: true,
    },
    showModelInfo: {
      type: Boolean,
      default: true,
    },
  })

  const emit = defineEmits([
    'update:modelValue',
    'file-upload',
    'location-created',
    'edit-counter',
    'delete-counter',
    'open-modele-dialog',
    'open-fournisseur-dialog',
    'open-fabricant-dialog',
    'open-famille-dialog',
    'open-lieu-dialog',
    'open-consommable-dialog',
    'search-equipment-models',
    'search-fournisseurs',
    'search-fabricants',
    'search-consumables',
  ])

  const handleFileUpload = (file) => {
    emit('file-upload', file)
  }

  const handleLocationCreated = (newLocation) => {
    emit('location-created', newLocation)
  }
</script>

<style scoped></style>
