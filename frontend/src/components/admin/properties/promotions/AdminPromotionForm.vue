<template>
  <!-- Pie fijo y opaco: la acción queda a la vista mientras el contenido scrollea. -->
  <div class="border-brand-divider sticky bottom-0 border-t bg-white px-5 py-4">
    <h3
      class="text-brand-muted mb-3 text-xs font-semibold tracking-wide uppercase"
    >
      Promoción
    </h3>

    <p
      v-if="successMessage"
      class="mb-3 rounded-xl border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700"
    >
      {{ successMessage }}
    </p>

    <p
      v-if="errorMessage"
      class="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600"
    >
      {{ errorMessage }}
    </p>

    <div class="space-y-3">
      <div class="flex items-start gap-3">
        <label
          class="text-brand-text w-24 shrink-0 pt-2 text-sm font-medium"
          for="promotion-days"
        >
          Duración
        </label>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <button
              v-for="preset in DAY_PRESETS"
              :key="preset"
              type="button"
              :disabled="saving"
              class="rounded-xl border px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50"
              :class="
                days === preset
                  ? 'border-brand-primary bg-brand-primary-light text-brand-primary'
                  : 'border-brand-border text-brand-muted hover:text-brand-text'
              "
              @click="days = preset"
            >
              {{ preset }}d
            </button>
            <input
              id="promotion-days"
              v-model.number="days"
              type="number"
              :min="MIN_DAYS"
              :max="MAX_DAYS"
              :disabled="saving"
              class="border-brand-border text-brand-text focus:border-brand-primary w-20 rounded-xl border px-3 py-1.5 text-sm transition-colors focus:outline-none disabled:opacity-50"
            />
          </div>
          <p class="text-brand-muted mt-1 text-xs">
            <template v-if="endsAt">Vence el {{ endsAt }}</template>
            <template v-else
              >Entre {{ MIN_DAYS }} y {{ MAX_DAYS }} días</template
            >
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <label
          class="text-brand-text w-24 shrink-0 text-sm font-medium"
          for="promotion-priority"
        >
          Prioridad
        </label>
        <div class="min-w-0 flex-1">
          <select
            id="promotion-priority"
            v-model.number="priority"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
          >
            <option v-for="level in PRIORITIES" :key="level" :value="level">
              {{ level }}
            </option>
          </select>
          <p class="text-brand-muted mt-1 text-xs">
            La más alta aparece primero en el feed.
          </p>
        </div>
      </div>
    </div>

    <div class="mt-4 flex items-center justify-end">
      <button
        type="button"
        :disabled="!canSubmit"
        class="bg-brand-primary flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-green-600 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40"
        @click="onSubmit"
      >
        <BaseSpinner v-if="saving" class="h-4 w-4 text-white" />
        {{ saving ? "Promocionando…" : "Promocionar" }}
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import { formatShortDate } from "@/utils/date";
import type { PromotionPayload } from "@/types/admin";

/**
 * Formulario de promoción. No llama a la API: emite duración y prioridad, y
 * quien lo recibe le pone la property que está seleccionada.
 */
const props = withDefaults(
  defineProps<{
    /** Reinicia el borrador al cambiar de property. */
    propertyId: string;
    saving?: boolean;
    successMessage?: string | null;
    errorMessage?: string | null;
  }>(),
  { saving: false, successMessage: null, errorMessage: null }
);

const emit = defineEmits<{ submit: [payload: PromotionPayload] }>();

/** El backend solo exige `ge=1`; el tope es de producto — una promoción no se vende indefinida. */
const MIN_DAYS = 1;
const MAX_DAYS = 60;
const DAY_PRESETS = [7, 15, 30];
const PRIORITIES = [1, 2, 3, 4, 5];

const days = ref<number>(DAY_PRESETS[0]);
const priority = ref<number>(PRIORITIES[0]);

const isValidDays = computed(
  () =>
    Number.isInteger(days.value) &&
    days.value >= MIN_DAYS &&
    days.value <= MAX_DAYS
);

/** `promoted_days` es abstracto; la fecha es lo que se quiere saber al elegirlo. */
const endsAt = computed(() => {
  if (!isValidDays.value) return "";
  const date = new Date();
  date.setDate(date.getDate() + days.value);
  return formatShortDate(date);
});

const canSubmit = computed(() => isValidDays.value && !props.saving);

function onSubmit() {
  emit("submit", { promotedDays: days.value, priority: priority.value });
}

watch(
  () => props.propertyId,
  () => {
    days.value = DAY_PRESETS[0];
    priority.value = PRIORITIES[0];
  }
);
</script>
