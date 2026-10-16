<template>
  <AdminStatusModal
    :entity="locality"
    noun="localidad"
    note="Sus barrios no cambian de estado."
    :saving="saving"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  />
</template>

<script lang="ts" setup>
import { watch } from "vue";
import AdminStatusModal from "@/components/admin/shared/AdminStatusModal.vue";
import { useUpdateLocality } from "@/composables/admin/useUpdateLocality";
import type { LocalityAdminRow } from "@/types/admin/catalog";

const { saving, error, update, reset } = useUpdateLocality();

const props = defineProps<{ locality: LocalityAdminRow | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

// Al reabrir no debe quedar el error del intento anterior.
watch(
  () => props.locality,
  (locality) => {
    if (locality) reset();
  }
);

const onSave = async () => {
  const locality = props.locality;
  if (!locality) return;
  if (await update(locality.id, { is_active: !locality.is_active }))
    emit("confirm");
};
</script>
