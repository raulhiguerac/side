<template>
  <AdminStatusModal
    :entity="neighborhood"
    noun="barrio"
    :saving="saving"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  />
</template>

<script lang="ts" setup>
import { watch } from "vue";
import AdminStatusModal from "@/components/admin/shared/AdminStatusModal.vue";
import { useUpdateNeighborhood } from "@/composables/admin/useUpdateNeighborhood";
import type { NeighborhoodAdminDetail } from "@/types/admin/catalog";

const { saving, error, update, reset } = useUpdateNeighborhood();

const props = defineProps<{ neighborhood: NeighborhoodAdminDetail | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

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
  if (await update(neighborhood.id, { is_active: !neighborhood.is_active }))
    emit("confirm");
};
</script>
