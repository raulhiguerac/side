<template>
  <AdminFormModal
    :open="country !== null"
    :icon="Pencil"
    title="Editar país"
    :subtitle="
      country
        ? `${country.iso_alpha2} · los códigos ISO no se editan`
        : undefined
    "
    submit-label="Guardar"
    saving-label="Guardando…"
    :saving="saving"
    :can-submit="isCountryFormValid(form)"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  >
    <CountryFormFields
      v-if="country"
      v-model:name="form.name"
      v-model:official-name="form.officialName"
      v-model:native-name="form.nativeName"
      v-model:phone-code="form.phoneCode"
      v-model:currency-code="form.currencyCode"
      v-model:default-locale="form.defaultLocale"
      v-model:default-timezone="form.defaultTimezone"
      v-model:is-supported="form.isSupported"
      class="mb-6"
      id-prefix="edit-country"
      :disabled="saving"
    />
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { reactive, watch } from "vue";
import { Pencil } from "@lucide/vue";
import CountryFormFields from "@/components/admin/catalog/countries/widgets/CountryFormFields.vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import { useUpdateCountry } from "@/composables/admin/useUpdateCountry";
import type { CountryAdminRow, CountryFormValues } from "@/types/admin/catalog";
import { isCountryFormValid, toCountryFields } from "@/utils/catalogForms";

const { saving, error, update, reset } = useUpdateCountry();

const props = defineProps<{ country: CountryAdminRow | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const form = reactive<CountryFormValues>({
  name: "",
  officialName: "",
  nativeName: "",
  phoneCode: "",
  currencyCode: "",
  defaultLocale: "",
  defaultTimezone: "",
  isSupported: false,
});

// El modal vive montado: los campos se cargan cada vez que se abre con un país.
watch(
  () => props.country,
  (country) => {
    if (!country) return;
    reset();
    Object.assign(form, {
      name: country.name,
      officialName: country.official_name ?? "",
      nativeName: country.native_name ?? "",
      phoneCode: country.phone_code,
      currencyCode: country.currency_code,
      defaultLocale: country.default_locale,
      defaultTimezone: country.default_timezone,
      isSupported: country.is_supported,
    });
  },
  { immediate: true }
);

const onSave = async () => {
  const country = props.country;
  if (!country || !isCountryFormValid(form)) return;
  if (await update(country.id, toCountryFields(form))) emit("confirm");
};
</script>
