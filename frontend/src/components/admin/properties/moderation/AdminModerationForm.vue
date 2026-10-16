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
      class="mb-3 rounded-xl border border-brand-success-border bg-brand-success-light px-3 py-2 text-sm text-brand-success"
    >
      {{ successMessage }}
    </p>

    <p
      v-if="errorMessage"
      class="mb-3 rounded-xl border border-brand-danger-border bg-brand-danger-light px-3 py-2 text-sm text-brand-danger"
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
          <BaseSelect
            id="moderation-verification"
            v-model="draftVerification"
            :disabled="saving"
          >
            <option
              v-for="option in verificationOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </BaseSelect>
          <p
            v-if="verificationChanged && draftVerification"
            class="text-brand-muted mt-1 text-xs"
          >
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
          <BaseSelect
            id="moderation-status"
            v-model="draftStatus"
            :disabled="saving"
          >
            <option
              v-for="option in statusOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </BaseSelect>
          <p
            v-if="statusChanged && draftStatus"
            class="text-brand-muted mt-1 text-xs"
          >
            {{ LISTING_STATUS_LABELS[status] }} →
            {{ LISTING_STATUS_LABELS[draftStatus] }}
          </p>
        </div>
      </div>

      <!-- Inline y no modal: el motivo es parte de elegir "Rechazada", que es donde el backend lo acepta. -->
      <div v-if="requiresReason">
        <FormField label="Motivo del rechazo *" input-id="moderation-reason">
          <BaseTextarea
            id="moderation-reason"
            v-model="reason"
            rows="3"
            maxlength="500"
            :disabled="saving"
            placeholder="Qué encontraste que impide aprobarla"
          />
        </FormField>
        <div class="mt-1 flex items-center justify-between">
          <p class="text-brand-muted text-xs">
            El propietario va a ver este texto.
          </p>
          <p class="text-brand-muted text-xs">{{ reason.length }}/500</p>
        </div>
      </div>
    </div>

    <div class="mt-4 flex items-center justify-end gap-2">
      <BaseButton
        variant="ghost"
        :disabled="!hasChanges || saving"
        @click="reset"
      >
        Descartar
      </BaseButton>
      <BaseButton :disabled="!canSave" :loading="saving" @click="onSave">
        {{ saving ? "Guardando…" : "Guardar" }}
      </BaseButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import FormField from "@/components/shared/form/FormField.vue";
import BaseSelect from "@/components/shared/form/BaseSelect.vue";
import BaseTextarea from "@/components/shared/form/BaseTextarea.vue";
import BaseButton from "@/components/shared/BaseButton.vue";
import { computed, ref, watch } from "vue";
import {
  LISTING_STATUS_LABELS,
  VERIFICATION_STATUS_LABELS,
} from "@/constants/propertyStatus";
import type { ModerationPayload } from "@/types/admin/moderation";
import type {
  ListingStatus,
  VerificationStatus,
} from "@/types/properties/base";

/** Acumula los cambios y los emite juntos: cambiar la verificación saca la fila del filtro. */
const props = withDefaults(
  defineProps<{
    status: ListingStatus | null;
    verificationStatus: VerificationStatus | null;
    /** Destinos legales del backend; vacío si la respuesta aún no los trae. */
    allowedVerificationTargets?: VerificationStatus[];
    allowedStatusTargets?: ListingStatus[];
    saving?: boolean;
    successMessage?: string | null;
    errorMessage?: string | null;
  }>(),
  {
    allowedVerificationTargets: () => [],
    allowedStatusTargets: () => [],
    saving: false,
    successMessage: null,
    errorMessage: null,
  }
);

const emit = defineEmits<{ save: [payload: ModerationPayload] }>();

const draftStatus = ref<ListingStatus | null>(null);
const draftVerification = ref<VerificationStatus | null>(null);
const reason = ref("");

/** El estado actual (primero, marcado) más los destinos que trajo el servidor. */
const verificationOptions = computed(() => {
  if (!props.verificationStatus) return [];
  const current = props.verificationStatus;
  return [
    {
      value: current,
      label: `${VERIFICATION_STATUS_LABELS[current]} (actual)`,
    },
    ...props.allowedVerificationTargets.map((target) => ({
      value: target,
      label: VERIFICATION_STATUS_LABELS[target],
    })),
  ];
});

const statusOptions = computed(() => {
  if (!props.status) return [];
  const current = props.status;
  return [
    { value: current, label: `${LISTING_STATUS_LABELS[current]} (actual)` },
    ...props.allowedStatusTargets.map((target) => ({
      value: target,
      label: LISTING_STATUS_LABELS[target],
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
