<template>
  <AdminFormModal
    :open="open"
    :icon="Plus"
    title="Crear país"
    submit-label="Crear"
    saving-label="Creando…"
    :saving="saving"
    :can-submit="canSubmit"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  >
    <div class="mb-6 space-y-3">
      <div class="grid grid-cols-3 gap-3">
        <div v-for="field in ISO_FIELDS" :key="field.key">
          <label
            class="text-brand-text mb-1 block text-sm font-medium"
            :for="`new-country-${field.key}`"
          >
            {{ field.label }}
          </label>
          <input
            :id="`new-country-${field.key}`"
            v-model="iso[field.key]"
            type="text"
            :maxlength="field.length"
            :placeholder="field.placeholder"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm uppercase transition-colors focus:outline-none disabled:opacity-50"
          />
        </div>
      </div>

      <CountryFormFields
        v-model:name="form.name"
        v-model:official-name="form.officialName"
        v-model:native-name="form.nativeName"
        v-model:phone-code="form.phoneCode"
        v-model:currency-code="form.currencyCode"
        v-model:default-locale="form.defaultLocale"
        v-model:default-timezone="form.defaultTimezone"
        v-model:is-supported="form.isSupported"
        id-prefix="new-country"
        :disabled="saving"
      />
    </div>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { computed, reactive, watch } from "vue";
import { Plus } from "@lucide/vue";
import CountryFormFields from "@/components/admin/catalog/countries/widgets/CountryFormFields.vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import { useCreateCountry } from "@/composables/admin/useCreateCountry";
import type { CountryFormValues } from "@/types/admin/catalog";
import {
  isCountryFormValid,
  isIsoCodeValid,
  toCountryFields,
} from "@/utils/catalogForms";

const { saving, error, create, reset } = useCreateCountry();

const props = defineProps<{ open: boolean }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const ISO_FIELDS = [
  { key: "alpha2", label: "ISO alfa-2", length: 2, placeholder: "CO" },
  { key: "alpha3", label: "ISO alfa-3", length: 3, placeholder: "COL" },
  { key: "numeric", label: "ISO numérico", length: 3, placeholder: "170" },
] as const;

const EMPTY_FORM: CountryFormValues = {
  name: "",
  officialName: "",
  nativeName: "",
  phoneCode: "",
  currencyCode: "",
  defaultLocale: "es",
  defaultTimezone: "",
  isSupported: false,
};

const iso = reactive({ alpha2: "", alpha3: "", numeric: "" });
const form = reactive<CountryFormValues>({ ...EMPTY_FORM });

// Cada apertura arranca con el formulario vacío.
watch(
  () => props.open,
  (open) => {
    if (!open) return;
    Object.assign(iso, { alpha2: "", alpha3: "", numeric: "" });
    Object.assign(form, EMPTY_FORM);
    reset();
  }
);

const canSubmit = computed(
  () => isIsoCodeValid(iso) && isCountryFormValid(form)
);

const onSave = async () => {
  if (!canSubmit.value) return;

  const created = await create({
    iso_alpha2: iso.alpha2.trim().toUpperCase(),
    iso_alpha3: iso.alpha3.trim().toUpperCase(),
    iso_numeric: iso.numeric.trim(),
    ...toCountryFields(form),
  });
  if (created) emit("confirm");
};
</script>
