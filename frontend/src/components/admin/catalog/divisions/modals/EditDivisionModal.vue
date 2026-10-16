<template>
  <AdminFormModal
    :open="division !== null"
    :icon="Pencil"
    title="Editar división"
    :subtitle="
      division ? `Código ${division.code} · el país no se edita` : undefined
    "
    submit-label="Guardar"
    saving-label="Guardando…"
    :saving="saving"
    :can-submit="isDivisionFormValid(form)"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  >
    <DivisionFormFields
      v-if="division"
      v-model:name="form.name"
      v-model:type-name="form.typeName"
      v-model:iso-code="form.isoCode"
      class="mb-6"
      id-prefix="edit-division"
      :disabled="saving"
    />
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { reactive, watch } from "vue";
import { Pencil } from "@lucide/vue";
import DivisionFormFields from "@/components/admin/catalog/divisions/widgets/DivisionFormFields.vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import { useUpdateDivision } from "@/composables/admin/useUpdateDivision";
import type {
  DivisionAdminRow,
  DivisionFormValues,
} from "@/types/admin/catalog";
import { isDivisionFormValid } from "@/utils/catalogForms";

const { saving, error, update, reset } = useUpdateDivision();

const props = defineProps<{ division: DivisionAdminRow | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const form = reactive<DivisionFormValues>({
  name: "",
  typeName: "",
  isoCode: "",
});

// El modal vive montado: los campos se cargan cada vez que se abre con una división.
watch(
  () => props.division,
  (division) => {
    if (!division) return;
    reset();
    Object.assign(form, {
      name: division.name,
      typeName: division.type_name,
      isoCode: division.iso_code ?? "",
    });
  },
  { immediate: true }
);

const onSave = async () => {
  const division = props.division;
  if (!division || !isDivisionFormValid(form)) return;

  const updated = await update(division.id, {
    name: form.name.trim(),
    type_name: form.typeName.trim(),
    iso_code: form.isoCode.trim() || null,
  });
  if (updated) emit("confirm");
};
</script>
