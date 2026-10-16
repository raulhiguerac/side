<template>
  <AdminFormModal
    :open="entity !== null"
    :icon="deactivating ? Ban : RotateCcw"
    :title="`${deactivating ? 'Desactivar' : 'Reactivar'} ${noun}`"
    :submit-label="deactivating ? 'Desactivar' : 'Reactivar'"
    saving-label="Guardando…"
    :saving="saving"
    :error="error"
    :danger="deactivating"
    @close="$emit('close')"
    @submit="$emit('submit')"
  >
    <p class="text-brand-muted mb-6 text-sm">
      <strong class="text-brand-text">{{ entity?.name }}</strong>
      {{
        deactivating
          ? "deja de aparecer en los listados públicos del catálogo."
          : "vuelve a aparecer en los listados públicos del catálogo."
      }}
      <template v-if="deactivating && note">{{ note }}</template>
    </p>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import { Ban, RotateCcw } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";

// Solo pinta: el PATCH lo hace el modal de cada entidad con su composable.
const props = defineProps<{
  entity: { name: string; is_active: boolean } | null;
  noun: string;
  /** Aclaración que se suma al desactivar. */
  note?: string;
  saving: boolean;
  error: string | null;
}>();

defineEmits<{ close: []; submit: [] }>();

const deactivating = computed(() => props.entity?.is_active ?? true);
</script>
