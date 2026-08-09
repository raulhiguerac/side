<template>
  <!-- Pie fijo y opaco: la moderación queda a la vista mientras el contenido scrollea. -->
  <div
    v-if="status && verificationStatus"
    class="border-brand-divider sticky bottom-0 border-t bg-white px-5 py-4"
  >
    <h3
      class="text-brand-muted mb-3 text-xs font-semibold tracking-wide uppercase"
    >
      Moderación
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
      <div class="flex items-center gap-3">
        <label
          for="moderation-verification"
          class="text-brand-text w-24 shrink-0 text-sm font-medium"
        >
          Verificación
        </label>
        <div class="min-w-0 flex-1">
          <select
            id="moderation-verification"
            v-model="draftVerification"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
          >
            <option
              v-for="option in verificationOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
          <p v-if="verificationChanged" class="text-brand-muted mt-1 text-xs">
            {{ VERIFICATION_STATUS_LABELS[verificationStatus] }} →
            {{ VERIFICATION_STATUS_LABELS[draftVerification] }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <label
          for="moderation-status"
          class="text-brand-text w-24 shrink-0 text-sm font-medium"
        >
          Estado
        </label>
        <div class="min-w-0 flex-1">
          <select
            id="moderation-status"
            v-model="draftStatus"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
          >
            <option
              v-for="option in statusOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
          <p v-if="statusChanged" class="text-brand-muted mt-1 text-xs">
            {{ LISTING_STATUS_LABELS[status] }} →
            {{ LISTING_STATUS_LABELS[draftStatus] }}
          </p>
        </div>
      </div>

      <!-- Inline y no modal: el motivo es parte de elegir "Rechazada", que es donde el backend lo acepta. -->
      <div v-if="requiresReason">
        <label
          for="moderation-reason"
          class="text-brand-text mb-1 block text-sm font-medium"
        >
          Motivo del rechazo *
        </label>
        <textarea
          id="moderation-reason"
          v-model="reason"
          rows="3"
          maxlength="500"
          :disabled="saving"
          placeholder="Qué encontraste que impide aprobarla"
          class="border-brand-border text-brand-text placeholder:text-brand-placeholder focus:border-brand-primary w-full resize-none rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
        />
        <div class="mt-1 flex items-center justify-between">
          <p class="text-brand-muted text-xs">
            El propietario va a ver este texto.
          </p>
          <p class="text-brand-muted text-xs">{{ reason.length }}/500</p>
        </div>
      </div>
    </div>

    <div class="mt-4 flex items-center justify-end gap-2">
      <button
        type="button"
        :disabled="!hasChanges || saving"
        class="text-brand-muted hover:bg-brand-bg rounded-xl px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40"
        @click="reset"
      >
        Descartar
      </button>
      <button
        type="button"
        :disabled="!canSave"
        class="bg-brand-primary flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-green-600 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40"
        @click="onSave"
      >
        <BaseSpinner v-if="saving" class="h-4 w-4 text-white" />
        {{ saving ? "Guardando…" : "Guardar" }}
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import {
  LISTING_STATUS_LABELS,
  VERIFICATION_STATUS_LABELS,
} from "@/constants/propertyStatus";
import {
  LISTING_STATUS_TRANSITIONS,
  VERIFICATION_TRANSITIONS,
} from "@/constants/moderationTransitions";
import type { ModerationPayload } from "@/types/admin";
import type { ListingStatus } from "@/types/feed";
import type { VerificationStatus } from "@/types/properties";

/** Acumula los cambios y los emite juntos: cambiar la verificación saca la fila del filtro. */
const props = defineProps<{
  status: ListingStatus | null;
  verificationStatus: VerificationStatus | null;
  saving?: boolean;
  successMessage?: string | null;
  errorMessage?: string | null;
}>();

const emit = defineEmits<{ save: [payload: ModerationPayload] }>();

const draftStatus = ref<ListingStatus | null>(null);
const draftVerification = ref<VerificationStatus | null>(null);
const reason = ref("");

/** El estado actual (primero, marcado) más sus destinos legales: lo que no está en la máquina no se ofrece. */
const verificationOptions = computed(() => {
  if (!props.verificationStatus) return [];
  const current = props.verificationStatus;
  return [
    {
      value: current,
      label: `${VERIFICATION_STATUS_LABELS[current]} (actual)`,
    },
    ...VERIFICATION_TRANSITIONS[current].map((action) => ({
      value: action.target,
      label: VERIFICATION_STATUS_LABELS[action.target],
    })),
  ];
});

const statusOptions = computed(() => {
  if (!props.status) return [];
  const current = props.status;
  return [
    { value: current, label: `${LISTING_STATUS_LABELS[current]} (actual)` },
    ...LISTING_STATUS_TRANSITIONS[current].map((action) => ({
      value: action.target,
      label: LISTING_STATUS_LABELS[action.target],
    })),
  ];
});

const verificationChanged = computed(
  () =>
    draftVerification.value !== null &&
    draftVerification.value !== props.verificationStatus
);

const statusChanged = computed(
  () => draftStatus.value !== null && draftStatus.value !== props.status
);

const hasChanges = computed(
  () => verificationChanged.value || statusChanged.value
);

const requiresReason = computed(
  () => verificationChanged.value && draftVerification.value === "rejected"
);

const canSave = computed(() => {
  if (!hasChanges.value || props.saving) return false;
  if (requiresReason.value && !reason.value.trim()) return false;
  return true;
});

function reset() {
  draftStatus.value = props.status;
  draftVerification.value = props.verificationStatus;
  reason.value = "";
}

function onSave() {
  emit("save", {
    ...(verificationChanged.value && draftVerification.value
      ? { verificationStatus: draftVerification.value }
      : {}),
    ...(requiresReason.value ? { rejectionReason: reason.value.trim() } : {}),
    ...(statusChanged.value && draftStatus.value
      ? { status: draftStatus.value }
      : {}),
  });
}

/** Cambiar de property —o recargarla tras guardar— reinicia el borrador. */
watch(() => [props.status, props.verificationStatus], reset, {
  immediate: true,
});
</script>
