<template>
  <BaseModal :model-value="isOpen" @update:model-value="$emit('close')">
    <div class="mb-4 flex items-center gap-4">
      <div
        class="flex h-12 w-12 items-center justify-center rounded-xl bg-red-100"
      >
        <Megaphone class="h-6 w-6 text-red-600" />
      </div>
      <h3 class="text-brand-text text-lg font-bold">Quitar promoción</h3>
    </div>

    <p class="text-brand-muted mb-6 text-sm">
      La propiedad deja de aparecer como destacada en el feed. Para volver a
      promocionarla hay que elegir duración y prioridad de nuevo.
    </p>

    <div class="flex gap-3">
      <button
        type="button"
        :disabled="removing"
        class="text-brand-text hover:bg-brand-bg flex-1 rounded-xl py-3 text-sm font-semibold transition-colors disabled:opacity-50"
        @click="$emit('close')"
      >
        Cancelar
      </button>
      <button
        type="button"
        :disabled="removing"
        class="flex-1 rounded-xl bg-red-500 py-3 text-sm font-semibold text-white transition-colors hover:bg-red-600 disabled:opacity-50"
        @click="$emit('confirm')"
      >
        {{ removing ? "Quitando…" : "Quitar" }}
      </button>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import { Megaphone } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";

/**
 * Solo confirma: el DELETE lo hace quien tiene la lista, que es el que después
 * la recarga. A diferencia de `DeletePropertyModal`, que se autogestiona y
 * reporta el fallo con un `alert()`.
 */
const props = defineProps<{
  propertyId: string | null;
  removing?: boolean;
}>();

defineEmits<{ close: []; confirm: [] }>();

const isOpen = computed(() => props.propertyId !== null);
</script>
