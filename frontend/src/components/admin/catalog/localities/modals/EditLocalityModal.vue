<template>
  <AdminFormModal
    :open="isOpen"
    :icon="Pencil"
    title="Editar localidad"
    :subtitle="
      locality
        ? `Código ${locality.code} · país y división no se editan`
        : undefined
    "
    submit-label="Guardar"
    saving-label="Guardando…"
    :saving="saving"
    :can-submit="isLocalityFormValid(form)"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  >
    <LocalityFormFields
      v-if="locality"
      v-model:name="form.name"
      v-model:local-name="form.localName"
      v-model:locality-type="form.localityType"
      v-model:timezone="form.timezone"
      v-model:latitude="form.latitude"
      v-model:longitude="form.longitude"
      v-model:is-capital="form.isCapital"
      class="mb-6"
      id-prefix="edit-locality"
      :disabled="saving"
    />
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { computed, reactive, watch } from "vue";
import { Pencil } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import LocalityFormFields from "@/components/admin/catalog/localities/widgets/LocalityFormFields.vue";
import { useUpdateLocality } from "@/composables/admin/useUpdateLocality";
import type {
  LocalityAdminRow,
  LocalityFormValues,
  LocalityUpdatePayload,
} from "@/types/admin/catalog";
import { isLocalityFormValid } from "@/utils/catalogForms";

const { saving, error, update, reset } = useUpdateLocality();

const props = defineProps<{ locality: LocalityAdminRow | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const isOpen = computed(() => props.locality !== null);

const form = reactive<LocalityFormValues>({
  name: "",
  localName: "",
  localityType: "city",
  timezone: "",
  latitude: "",
  longitude: "",
  isCapital: false,
});

// El modal vive montado: los campos se cargan cada vez que se abre con una localidad.
watch(
  () => props.locality,
  (locality) => {
    if (!locality) return;
    reset();
    Object.assign(form, {
      name: locality.name,
      localName: locality.local_name ?? "",
      localityType: locality.locality_type,
      timezone: locality.timezone,
      latitude: locality.point.latitude,
      longitude: locality.point.longitude,
      isCapital: locality.is_capital,
    });
  },
  { immediate: true }
);

const onSave = async () => {
  const locality = props.locality;
  const { latitude, longitude } = form;
  if (!locality || !isLocalityFormValid(form)) return;
  if (typeof latitude !== "number" || typeof longitude !== "number") return;

  const payload: LocalityUpdatePayload = {
    name: form.name.trim(),
    local_name: form.localName.trim() || null,
    locality_type: form.localityType,
    timezone: form.timezone.trim(),
    latitude,
    longitude,
    is_capital: form.isCapital,
  };

  if (await update(locality.id, payload)) emit("confirm");
};
</script>
