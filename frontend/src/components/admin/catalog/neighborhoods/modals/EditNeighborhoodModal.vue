<template>
  <AdminFormModal
    :open="isOpen"
    :icon="Pencil"
    title="Editar barrio"
    :subtitle="neighborhood ? `Código ${neighborhood.code}` : undefined"
    submit-label="Guardar"
    saving-label="Guardando…"
    :saving="saving"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  >
    <div v-if="neighborhood" class="mb-6 space-y-3">
      <div>
        <FormField label="Nombre" input-id="neighborhood-name">
          <BaseInput id="neighborhood-name" type="text" v-model="name" />
        </FormField>
      </div>

      <div>
        <FormField label="Código postal" input-id="neighborhood-postal-code">
          <BaseInput
            id="neighborhood-postal-code"
            type="text"
            v-model="postalCode"
          />
        </FormField>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <FormField label="Latitud" input-id="neighborhood-latitude">
            <BaseInput
              id="neighborhood-latitude"
              type="number"
              step="any"
              v-model.number="latitude"
              class="tabular-nums"
            />
          </FormField>
        </div>
        <div>
          <FormField label="Longitud" input-id="neighborhood-longitude">
            <BaseInput
              id="neighborhood-longitude"
              type="number"
              step="any"
              v-model.number="longitude"
              class="tabular-nums"
            />
          </FormField>
        </div>
      </div>
    </div>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import FormField from "@/components/shared/form/FormField.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
import { computed, ref, watch } from "vue";
import { Pencil } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import type { NeighborhoodAdminDetail } from "@/types/admin/catalog";
import { useUpdateNeighborhood } from "@/composables/admin/useUpdateNeighborhood";
import type { NeighborhoodUpdatePayload } from "@/types/admin/catalog";

const { saving, error, update, reset } = useUpdateNeighborhood();

const props = defineProps<{ neighborhood: NeighborhoodAdminDetail | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const isOpen = computed(() => props.neighborhood !== null);

const name = ref("");
const postalCode = ref("");
const latitude = ref(0);
const longitude = ref(0);

// El modal vive montado: los campos se cargan cada vez que se abre con un barrio.
watch(
  () => props.neighborhood,
  (neighborhood) => {
    if (!neighborhood) return;
    reset();
    name.value = neighborhood.name;
    postalCode.value = neighborhood.postal_code ?? "";
    latitude.value = neighborhood.latitude;
    longitude.value = neighborhood.longitude;
  },
  { immediate: true }
);

const onSave = async () => {
  const neighborhood = props.neighborhood;
  if (!neighborhood) return;

  const payload: NeighborhoodUpdatePayload = {
    name: name.value,
    postal_code: postalCode.value.trim() || null,
    latitude: latitude.value,
    longitude: longitude.value,
  };

  const updated = await update(neighborhood.id, payload);
  if (updated) emit("confirm");
};
</script>
