<template>
  <AdminStatusModal
    :entity="country"
    noun="país"
    note="Sus divisiones y localidades no cambian de estado."
    :saving="saving"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  />
</template>

<script lang="ts" setup>
import { watch } from "vue";
import AdminStatusModal from "@/components/admin/shared/AdminStatusModal.vue";
import { useUpdateCountry } from "@/composables/admin/useUpdateCountry";
import type { CountryAdminRow } from "@/types/admin/catalog";

const { saving, error, update, reset } = useUpdateCountry();

const props = defineProps<{ country: CountryAdminRow | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

// Al reabrir no debe quedar el error del intento anterior.
watch(
  () => props.country,
  (country) => {
    if (country) reset();
  }
);

const onSave = async () => {
  const country = props.country;
  if (!country) return;
  if (await update(country.id, { is_active: !country.is_active }))
    emit("confirm");
};
</script>
