<template>
  <AdminFormModal
    :open="open"
    :icon="Plus"
    title="Crear división"
    submit-label="Crear"
    saving-label="Creando…"
    :saving="saving"
    :can-submit="canSubmit"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  >
    <div class="mb-6 space-y-3">
      <CascadeSelectFields
        v-model="place"
        id-prefix="new-division"
        :fields="CASCADE"
        :disabled="saving"
      />

      <div>
        <FormField label="Código" input-id="new-division-code">
          <BaseInput
            id="new-division-code"
            v-model="code"
            type="text"
            maxlength="20"
            placeholder="Obligatorio, p. ej. el código DANE"
            :disabled="saving"
          />
        </FormField>
      </div>

      <DivisionFormFields
        v-model:name="form.name"
        v-model:type-name="form.typeName"
        v-model:iso-code="form.isoCode"
        id-prefix="new-division"
        :disabled="saving"
      />
    </div>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import FormField from "@/components/shared/form/FormField.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
import { computed, reactive, ref, watch } from "vue";
import { Plus } from "@lucide/vue";
import DivisionFormFields from "@/components/admin/catalog/divisions/widgets/DivisionFormFields.vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import CascadeSelectFields from "@/components/admin/shared/CascadeSelectFields.vue";
import { useCreateDivision } from "@/composables/admin/useCreateDivision";
import { COUNTRY_SELECT } from "@/constants/catalogFilters";
import type { DivisionFormValues } from "@/types/admin/catalog";
import { isDivisionFormValid } from "@/utils/catalogForms";

const CASCADE = [COUNTRY_SELECT];

const { saving, error, create, reset } = useCreateDivision();

// El país arranca con el del filtro aplicado, si hay.
const props = defineProps<{ open: boolean; initialCountryId: string | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const EMPTY_FORM: DivisionFormValues = { name: "", typeName: "", isoCode: "" };

const place = ref<Record<string, string>>({});
const code = ref("");
const form = reactive<DivisionFormValues>({ ...EMPTY_FORM });

// Cada apertura arranca con el formulario vacío.
watch(
  () => props.open,
  (open) => {
    if (!open) return;
    code.value = "";
    Object.assign(form, EMPTY_FORM);
    reset();
    place.value = { country_id: props.initialCountryId ?? "" };
  }
);

const canSubmit = computed(
  () =>
    !!place.value.country_id &&
    code.value.trim() !== "" &&
    isDivisionFormValid(form)
);

const onSave = async () => {
  if (!canSubmit.value) return;

  const created = await create({
    country_id: place.value.country_id,
    code: code.value.trim(),
    name: form.name.trim(),
    type_name: form.typeName.trim(),
    iso_code: form.isoCode.trim() || null,
  });
  if (created) emit("confirm");
};
</script>
