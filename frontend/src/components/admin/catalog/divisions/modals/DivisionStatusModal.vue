<template>
  <AdminStatusModal
    :entity="division"
    noun="división"
    note="Sus localidades no cambian de estado."
    :saving="saving"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  />
</template>

<script lang="ts" setup>
import { watch } from "vue";
import AdminStatusModal from "@/components/admin/shared/AdminStatusModal.vue";
import { useUpdateDivision } from "@/composables/admin/useUpdateDivision";
import type { DivisionAdminRow } from "@/types/admin/catalog";

const { saving, error, update, reset } = useUpdateDivision();

const props = defineProps<{ division: DivisionAdminRow | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

// Al reabrir no debe quedar el error del intento anterior.
watch(
  () => props.division,
  (division) => {
    if (division) reset();
  }
);

const onSave = async () => {
  const division = props.division;
  if (!division) return;
  if (await update(division.id, { is_active: !division.is_active }))
    emit("confirm");
};
</script>
