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
        <label
          class="text-brand-text mb-1 block text-sm font-medium"
          for="neighborhood-name"
        >
          Nombre
        </label>
        <input
          id="neighborhood-name"
          type="text"
          v-model="name"
          class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none"
        />
      </div>

      <div>
        <label
          class="text-brand-text mb-1 block text-sm font-medium"
          for="neighborhood-postal-code"
        >
          Código postal
        </label>
        <input
          id="neighborhood-postal-code"
          type="text"
          v-model="postalCode"
          class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label
            class="text-brand-text mb-1 block text-sm font-medium"
            for="neighborhood-latitude"
          >
            Latitud
          </label>
          <input
            id="neighborhood-latitude"
            type="number"
            step="any"
            v-model.number="latitude"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm tabular-nums transition-colors focus:outline-none"
          />
        </div>
        <div>
          <label
            class="text-brand-text mb-1 block text-sm font-medium"
            for="neighborhood-longitude"
          >
            Longitud
          </label>
          <input
            id="neighborhood-longitude"
            type="number"
            step="any"
            v-model.number="longitude"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm tabular-nums transition-colors focus:outline-none"
          />
        </div>
      </div>
    </div>
  </AdminFormModal>
</template>

<script lang="ts" setup>
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
