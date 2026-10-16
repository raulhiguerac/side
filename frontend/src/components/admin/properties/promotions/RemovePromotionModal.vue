<template>
  <AdminFormModal
    :open="isOpen"
    :icon="Megaphone"
    title="Quitar promoción"
    submit-label="Quitar"
    saving-label="Quitando…"
    :saving="removing"
    danger
    @close="$emit('close')"
    @submit="$emit('confirm')"
  >
    <p class="text-brand-muted mb-6 text-sm">
      La propiedad deja de aparecer como destacada en el feed. Para volver a
      promocionarla hay que elegir duración y prioridad de nuevo.
    </p>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import { Megaphone } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";

// Solo confirma: el DELETE lo hace quien tiene la lista.
const props = defineProps<{
  propertyId: string | null;
  removing?: boolean;
}>();

defineEmits<{ close: []; confirm: [] }>();

const isOpen = computed(() => props.propertyId !== null);
</script>
