<template>
  <BaseModal :model-value="isOpen" @update:model-value="$emit('close')">
    <div class="mb-4 flex items-center gap-4">
      <div
        :class="[
          'flex h-12 w-12 items-center justify-center rounded-xl',
          deactivating ? 'bg-red-100' : 'bg-brand-primary-light',
        ]"
      >
        <Ban v-if="deactivating" class="h-6 w-6 text-red-600" />
        <RotateCcw v-else class="text-brand-primary h-6 w-6" />
      </div>
      <h3 class="text-brand-text text-lg font-bold">
        {{ deactivating ? "Desactivar barrio" : "Reactivar barrio" }}
      </h3>
    </div>

    <p class="text-brand-muted mb-6 text-sm">
      <template v-if="deactivating">
        <strong class="text-brand-text">{{ neighborhood?.name }}</strong> deja
        de aparecer en los listados públicos del catálogo.
      </template>
      <template v-else>
        <strong class="text-brand-text">{{ neighborhood?.name }}</strong> vuelve
        a aparecer en los listados públicos del catálogo.
      </template>
    </p>

    <FormMessage v-if="error" variant="error" class="mb-4">
      {{ error }}
    </FormMessage>

    <div class="flex gap-3">
      <button
        type="button"
        :disabled="saving"
        class="text-brand-text hover:bg-brand-bg flex-1 rounded-xl py-3 text-sm font-semibold transition-colors disabled:opacity-50"
        @click="$emit('close')"
      >
        Cancelar
      </button>
      <button
        type="button"
        :disabled="saving"
        :class="[
          'flex-1 rounded-xl py-3 text-sm font-semibold text-white transition-colors disabled:opacity-50',
          deactivating
            ? 'bg-red-500 hover:bg-red-600'
            : 'bg-brand-primary hover:opacity-90',
        ]"
        @click="onSave"
      >
        <template v-if="saving">Guardando…</template>
        <template v-else>
          {{ deactivating ? "Desactivar" : "Reactivar" }}
        </template>
      </button>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import { computed, watch } from "vue";
import { Ban, RotateCcw } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import { useUpdateNeighborhood } from "@/composables/admin/useUpdateNeighborhood";
import type {
  NeighborhoodAdminDetail,
  NeighborhoodUpdatePayload,
} from "@/types/admin/catalog";

const { saving, error, update, reset } = useUpdateNeighborhood();

const props = defineProps<{ neighborhood: NeighborhoodAdminDetail | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const isOpen = computed(() => props.neighborhood !== null);
const deactivating = computed(() => props.neighborhood?.is_active ?? true);

// Al reabrir no debe quedar el error del intento anterior.
watch(
  () => props.neighborhood,
  (neighborhood) => {
    if (neighborhood) reset();
  }
);

const onSave = async () => {
  const neighborhood = props.neighborhood;
  if (!neighborhood) return;

  const payload: NeighborhoodUpdatePayload = {
    is_active: !neighborhood.is_active,
  };

  const updated = await update(neighborhood.id, payload);
  if (updated) emit("confirm");
};
</script>
