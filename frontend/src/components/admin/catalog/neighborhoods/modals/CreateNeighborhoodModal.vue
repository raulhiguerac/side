<template>
  <AdminFormModal
    :open="open"
    :icon="Plus"
    title="Crear barrio"
    subtitle="Sin geometría: se sube después"
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
        id-prefix="new-neighborhood"
        :fields="CASCADE"
        :disabled="saving"
      />

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label
            class="text-brand-text mb-1 block text-sm font-medium"
            for="new-neighborhood-code"
          >
            Código
          </label>
          <input
            id="new-neighborhood-code"
            placeholder="Obligatorio"
            v-model="code"
            type="text"
            maxlength="30"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
          />
        </div>
        <div>
          <label
            class="text-brand-text mb-1 block text-sm font-medium"
            for="new-neighborhood-postal-code"
          >
            Código postal
          </label>
          <input
            id="new-neighborhood-postal-code"
            v-model="postalCode"
            type="text"
            maxlength="20"
            placeholder="Opcional"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
          />
        </div>
      </div>

      <div>
        <label
          class="text-brand-text mb-1 block text-sm font-medium"
          for="new-neighborhood-name"
        >
          Nombre
        </label>
        <input
          id="new-neighborhood-name"
          placeholder="Obligatorio"
          v-model="name"
          type="text"
          maxlength="150"
          :disabled="saving"
          class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label
            class="text-brand-text mb-1 block text-sm font-medium"
            for="new-neighborhood-latitude"
          >
            Latitud
          </label>
          <input
            id="new-neighborhood-latitude"
            placeholder="Obligatoria, entre -90 y 90"
            v-model.number="latitude"
            type="number"
            step="any"
            min="-90"
            max="90"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm tabular-nums transition-colors focus:outline-none disabled:opacity-50"
          />
        </div>
        <div>
          <label
            class="text-brand-text mb-1 block text-sm font-medium"
            for="new-neighborhood-longitude"
          >
            Longitud
          </label>
          <input
            id="new-neighborhood-longitude"
            placeholder="Obligatoria, entre -180 y 180"
            v-model.number="longitude"
            type="number"
            step="any"
            min="-180"
            max="180"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm tabular-nums transition-colors focus:outline-none disabled:opacity-50"
          />
        </div>
      </div>
    </div>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { Plus } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import CascadeSelectFields from "@/components/admin/shared/CascadeSelectFields.vue";
import { COUNTRY_SELECT, LOCALITY_SELECT } from "@/constants/catalogFilters";
import { useCreateNeighborhood } from "@/composables/admin/useCreateNeighborhood";
import type { NeighborhoodCreatePayload } from "@/types/admin/catalog";

const { saving, error, create, reset } = useCreateNeighborhood();
const CASCADE = [COUNTRY_SELECT, LOCALITY_SELECT];
const place = ref<Record<string, string>>({});
const localityId = computed(() => place.value.locality_id ?? "");

// País y localidad arrancan con los del filtro aplicado, si hay.
const props = defineProps<{
  open: boolean;
  initialCountryId: string | null;
  initialLocalityId: string | null;
}>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const code = ref("");
const name = ref("");
const postalCode = ref("");
// `v-model.number` deja "" si el campo queda vacío.
const latitude = ref<number | "">("");
const longitude = ref<number | "">("");

const inRange = (value: number | "", limit: number) =>
  typeof value === "number" && Math.abs(value) <= limit;

// El backend no valida largo ni rango: se exige acá.
const canSubmit = computed(
  () =>
    localityId.value !== "" &&
    code.value.trim() !== "" &&
    name.value.trim() !== "" &&
    inRange(latitude.value, 90) &&
    inRange(longitude.value, 180)
);

// Cada apertura arranca con el formulario vacío.
watch(
  () => props.open,
  (open) => {
    if (!open) return;
    code.value = "";
    name.value = "";
    postalCode.value = "";
    latitude.value = "";
    longitude.value = "";
    reset();
    place.value = {
      country_id: props.initialCountryId ?? "",
      locality_id: props.initialLocalityId ?? "",
    };
  }
);

const onSave = async () => {
  const lat = latitude.value;
  const lng = longitude.value;
  if (!canSubmit.value) return;
  if (typeof lat !== "number" || typeof lng !== "number") return;

  const payload: NeighborhoodCreatePayload = {
    locality_id: localityId.value,
    code: code.value.trim(),
    name: name.value.trim(),
    postal_code: postalCode.value.trim() || null,
    latitude: lat,
    longitude: lng,
  };

  const created = await create(payload);
  if (created) emit("confirm");
};
</script>
