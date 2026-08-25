<template>
  <div class="border-brand-divider overflow-hidden rounded-2xl border bg-white">
    <div class="border-brand-divider border-b px-5 py-4">
      <h2 class="text-brand-text font-mono text-sm font-semibold">
        Job {{ job ? job.id.slice(0, 8) : "—" }}
      </h2>
      <p class="text-brand-muted mt-0.5 text-xs">
        {{
          job ? formatLongDateTime(job.created_at) : "Ninguna corrida elegida"
        }}
      </p>
    </div>

    <p v-if="!job" class="text-brand-muted px-5 py-12 text-center text-sm">
      Elegí una importación de la tabla.
    </p>

    <template v-else>
      <div class="border-brand-divider border-b px-5 py-4">
        <span
          :class="[
            'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
            BULK_JOB_STATUS_BADGE_CLASSES[job.status],
          ]"
        >
          {{ BULK_JOB_STATUS_LABELS[job.status] }}
        </span>

        <dl class="mt-4 space-y-2 text-sm">
          <div class="flex justify-between">
            <dt class="text-brand-muted">Cargadas</dt>
            <dd class="text-brand-text font-semibold tabular-nums">
              {{ job.inserted.toLocaleString("es-CO") }}
            </dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-brand-muted">Con error</dt>
            <dd
              :class="[
                'font-semibold tabular-nums',
                job.error_count ? 'text-red-600' : 'text-brand-text',
              ]"
            >
              {{ job.error_count.toLocaleString("es-CO") }}
            </dd>
          </div>
          <!-- Derivada, no guardada: cada fila del CSV o entra o falla. -->
          <div class="flex justify-between">
            <dt class="text-brand-muted">Leídas</dt>
            <dd class="text-brand-text tabular-nums">
              {{ rowsRead.toLocaleString("es-CO") }}
            </dd>
          </div>
        </dl>
      </div>

      <div class="border-brand-divider border-b px-5 py-4">
        <h3
          class="text-brand-muted mb-3 text-xs font-semibold tracking-wide uppercase"
        >
          Errores por fila
        </h3>

        <div v-if="loading" class="flex justify-center py-6">
          <BaseSpinner class="text-brand-primary h-5 w-5" />
        </div>

        <p
          v-else-if="error"
          class="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600"
        >
          {{ error }}
        </p>

        <p v-else-if="!errors.length" class="text-brand-muted text-sm">
          Ninguna fila quedó afuera.
        </p>

        <!-- Con miles de errores esta lista es inútil; el archivo es la salida real. -->
        <ul v-else class="max-h-64 space-y-3 overflow-y-auto">
          <li v-for="rowError in errors" :key="rowError.line">
            <p class="text-brand-text text-sm font-medium">
              L.{{ rowError.line }}
              <span class="text-brand-muted font-mono text-xs">
                {{ rowError.ref }}
              </span>
            </p>
            <ul class="mt-1 space-y-0.5">
              <li
                v-for="issue in rowError.issues"
                :key="issue"
                class="text-brand-muted text-xs"
              >
                · {{ issue }}
              </li>
            </ul>
          </li>
        </ul>
      </div>

      <div class="px-5 py-4">
        <p class="text-brand-muted mb-3 text-xs">
          Reprocesa el mismo archivo. Las filas ya cargadas se actualizan, no se
          duplican.
        </p>
        <button
          type="button"
          :disabled="!canRetry"
          class="bg-brand-primary flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-bold text-white transition-all duration-200 hover:bg-green-600 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RotateCcw class="h-4 w-4" />
          Relanzar job
        </button>
        <p v-if="isExpired" class="text-brand-muted mt-2 text-center text-xs">
          El CSV ya venció en storage.
        </p>
      </div>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { RotateCcw } from "@lucide/vue";
import propertiesApi from "@/api/propertiesApi";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import {
  BULK_JOB_STATUS_LABELS,
  BULK_JOB_STATUS_BADGE_CLASSES,
} from "@/constants/bulkJobStatus";
import type {
  BulkJobRow,
  BulkJobRowError,
  BulkJobStatusDetail,
} from "@/types/admin";

/** El detalle de una corrida: la fila llega entera desde el listado y acá solo
 * se piden los errores, que ese listado cuenta pero no trae. */
const props = defineProps<{ job: BulkJobRow | null }>();

const errors = ref<BulkJobRowError[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const longDateTimeFormatter = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "long",
  timeStyle: "short",
});

function formatLongDateTime(value: string): string {
  return longDateTimeFormatter.format(new Date(value));
}

const rowsRead = computed(() =>
  props.job ? props.job.inserted + props.job.error_count : 0
);

/** Sin archivo en storage no hay nada que reprocesar, y una corrida en curso no se toca. */
const isExpired = computed(
  () => !!props.job && new Date(props.job.expires_at) < new Date()
);

const canRetry = computed(
  () => !!props.job && props.job.status !== "pending" && !isExpired.value
);

/** Clickear filas rápido pisa las respuestas: el token descarta las que no son de la última. */
let requestToken = 0;

async function loadErrors(job: BulkJobRow | null) {
  const token = ++requestToken;

  errors.value = [];
  error.value = null;

  // Sin errores contados no hay request que hacer: el listado ya dijo que son cero.
  if (!job || !job.error_count) {
    loading.value = false;
    return;
  }

  loading.value = true;

  try {
    const { data } = await propertiesApi.get<BulkJobStatusDetail>(
      PROPERTIES_ENDPOINTS.adminBulkJobStatus(job.id)
    );
    if (token !== requestToken) return;
    errors.value = data.errors;
  } catch (e) {
    if (token !== requestToken) return;
    error.value = "No se pudieron cargar los errores de la corrida";
    console.error("admin bulk job errors failed", e);
  } finally {
    if (token === requestToken) loading.value = false;
  }
}

watch(() => props.job, loadErrors, { immediate: true });
</script>
