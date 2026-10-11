<template>
  <BaseModal :model-value="isOpen" @update:model-value="$emit('close')">
    <div class="mb-4 flex items-center gap-4">
      <div
        class="bg-brand-primary-light flex h-12 w-12 items-center justify-center rounded-xl"
      >
        <Plus class="text-brand-primary h-6 w-6" />
      </div>
      <div class="min-w-0">
        <h3 class="text-brand-text text-lg font-bold">Crear barrio</h3>
        <p class="text-brand-muted text-sm">Sin geometría: se sube después</p>
      </div>
    </div>

    <div class="mb-6 space-y-3">
      <LocalitySelectFields
        v-model:country-id="countryId"
        v-model:locality-id="localityId"
        id-prefix="new-neighborhood"
        :country-options="countryOptions"
        :locality-options="localityOptions"
        :loading-localities="loadingLocalities"
        :disabled="saving"
        @country-change="onCountryChange"
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

    <FormMessage v-if="error || optionsError" variant="error" class="mb-4">
      {{ error ?? optionsError }}
    </FormMessage>

    <div class="flex gap-3">
      <button
        type="button"
        :disabled="saving"
        class="text-brand-text hover:bg-brand-bg flex-1 rounded-xl py-3 text-sm font-semibold transition-colors disabled:opacity-50"
        @click="$emit('close')"
      >
        Cancelar
      </button>
      <button
        type="button"
        :disabled="!submittable"
        class="bg-brand-primary flex-1 rounded-xl py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        @click="onSave"
      >
        {{ saving ? "Creando…" : "Crear" }}
      </button>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { Plus } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import LocalitySelectFields from "@/components/admin/catalog/neighborhoods/widgets/LocalitySelectFields.vue";
import { useCreateNeighborhood } from "@/composables/admin/useCreateNeighborhood";
import { useLocalityPicker } from "@/composables/admin/useLocalityPicker";
import type { NeighborhoodCreatePayload } from "@/types/admin/catalog";

const { saving, error, create, reset } = useCreateNeighborhood();
const {
  countryId,
  localityId,
  countryOptions,
  localityOptions,
  loadingLocalities,
  error: optionsError,
  prefill,
  onCountryChange,
} = useLocalityPicker();

// País y localidad arrancan con los del filtro aplicado, si hay.
const props = defineProps<{
  open: boolean;
  initialCountryId: string | null;
  initialLocalityId: string | null;
}>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const isOpen = computed(() => props.open);

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

const submittable = computed(() => canSubmit.value && !saving.value);

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
    prefill(props.initialCountryId, props.initialLocalityId);
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
