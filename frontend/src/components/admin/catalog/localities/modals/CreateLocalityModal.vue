<template>
  <AdminFormModal
    :open="open"
    :icon="Plus"
    title="Crear localidad"
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
        id-prefix="new-locality"
        :fields="CASCADE"
        :disabled="saving"
      />

      <div>
        <label :class="LABEL_CLASSES" for="new-locality-code">Código</label>
        <input
          id="new-locality-code"
          v-model="code"
          type="text"
          maxlength="20"
          placeholder="Obligatorio"
          :disabled="saving"
          :class="FIELD_CLASSES"
        />
      </div>

      <LocalityFormFields
        v-model:name="form.name"
        v-model:local-name="form.localName"
        v-model:locality-type="form.localityType"
        v-model:timezone="form.timezone"
        v-model:latitude="form.latitude"
        v-model:longitude="form.longitude"
        v-model:is-capital="form.isCapital"
        id-prefix="new-locality"
        :disabled="saving"
      />
    </div>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from "vue";
import { Plus } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import CascadeSelectFields from "@/components/admin/shared/CascadeSelectFields.vue";
import { COUNTRY_SELECT, DIVISION_SELECT } from "@/constants/catalogFilters";
import LocalityFormFields from "@/components/admin/catalog/localities/widgets/LocalityFormFields.vue";
import { useCreateLocality } from "@/composables/admin/useCreateLocality";
import type {
  LocalityCreatePayload,
  LocalityFormValues,
} from "@/types/admin/catalog";
import { isLocalityFormValid } from "@/utils/catalogForms";

const { saving, error, create, reset } = useCreateLocality();
const CASCADE = [COUNTRY_SELECT, DIVISION_SELECT];
const place = ref<Record<string, string>>({});

// País y división arrancan con los del filtro aplicado, si hay.
const props = defineProps<{
  open: boolean;
  initialCountryId: string | null;
  initialDivisionId: string | null;
}>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const EMPTY_FORM: LocalityFormValues = {
  name: "",
  localName: "",
  localityType: "city",
  timezone: "",
  latitude: "",
  longitude: "",
  isCapital: false,
};

const code = ref("");
const form = reactive<LocalityFormValues>({ ...EMPTY_FORM });

// Cada apertura arranca con el formulario vacío.
watch(
  () => props.open,
  (open) => {
    if (!open) return;
    code.value = "";
    Object.assign(form, EMPTY_FORM);
    reset();
    place.value = {
      country_id: props.initialCountryId ?? "",
      admin_division_id: props.initialDivisionId ?? "",
    };
  }
);

const canSubmit = computed(
  () =>
    !!place.value.admin_division_id &&
    code.value.trim() !== "" &&
    isLocalityFormValid(form)
);

const onSave = async () => {
  const { latitude, longitude } = form;
  if (!canSubmit.value) return;
  if (typeof latitude !== "number" || typeof longitude !== "number") return;

  const payload: LocalityCreatePayload = {
    country_id: place.value.country_id,
    admin_division_id: place.value.admin_division_id,
    code: code.value.trim(),
    name: form.name.trim(),
    local_name: form.localName.trim() || null,
    locality_type: form.localityType,
    timezone: form.timezone.trim(),
    latitude,
    longitude,
    is_capital: form.isCapital,
  };

  if (await create(payload)) emit("confirm");
};

const LABEL_CLASSES = "text-brand-text mb-1 block text-sm font-medium";
const FIELD_CLASSES =
  "border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border bg-white px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50";
</script>
