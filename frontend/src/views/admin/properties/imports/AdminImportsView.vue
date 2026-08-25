<template>
  <div>
    <div class="mb-6 flex justify-end">
      <button
        @click="isBulkModalOpen = true"
        class="bg-brand-primary flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
      >
        <Upload class="h-4 w-4" />
        Importar CSV
      </button>
    </div>

    <AdminSplitView :error="error">
      <template #filters>
        <AdminFilterBar
          :filters="BULK_JOB_FILTERS"
          :initial="urlFilters"
          :loading="loading"
          @apply="onApplyFilters"
        />
      </template>

      <template #table>
        <AdminBulkJobsTable
          :rows="jobs"
          :loading="loading"
          :selected-id="selectedId"
          @row-click="selectedId = $event.id"
        />
      </template>

      <template #footer>
        <div
          v-if="total"
          class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-between"
        >
          <p class="text-brand-muted text-sm">
            Mostrando {{ range.from }}-{{ range.to }} de
            {{ total.toLocaleString("es-CO") }}
          </p>
          <PaginationArrows
            :has-prev="hasPrev"
            :has-next="hasNext"
            @prev="prev"
            @next="next"
          />
        </div>
      </template>

      <template #panel>
        <AdminBulkJobPanel :job="selectedJob" />
      </template>
    </AdminSplitView>

    <BulkUploadPropertiesModal v-model="isBulkModalOpen" />
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Upload } from "@lucide/vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminBulkJobsTable from "@/components/admin/properties/imports/AdminBulkJobsTable.vue";
import AdminBulkJobPanel from "@/components/admin/properties/imports/AdminBulkJobPanel.vue";
import BulkUploadPropertiesModal from "@/components/admin/properties/imports/BulkUploadPropertiesModal.vue";
import { useBulkJobs } from "@/composables/admin/useBulkJobs";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import { BULK_JOB_STATUS_LABELS } from "@/constants/bulkJobStatus";
import { sanitizeFilterQuery } from "@/utils/adminFilters";
import type { AdminFilterDefinition } from "@/types/admin";

/** `has_errors` va como select de dos opciones: el backend lo recibe como bool y
 * Pydantic parsea el `"true"`/`"false"` de la query. Las fechas todavía no. */
const BULK_JOB_FILTERS: readonly AdminFilterDefinition[] = [
  {
    key: "status",
    label: "Estado",
    options: BULK_JOB_STATUS_LABELS,
    allLabel: "Todos",
  },
  {
    key: "has_errors",
    label: "Errores",
    options: { true: "Con errores", false: "Sin errores" },
    allLabel: "Todas",
  },
];

const route = useRoute();
const router = useRouter();

const isBulkModalOpen = ref(false);

const {
  jobs,
  total,
  range,
  hasPrev,
  hasNext,
  loading,
  error,
  applyFilters,
  next,
  prev,
} = useBulkJobs();

const { selectedId } = useRowSelection(jobs);

/** El panel necesita la fila entera, no solo el id: de ahí salen `expires_at` y
 * el estado que deciden si se puede relanzar. */
const selectedJob = computed(
  () => jobs.value.find((job) => job.id === selectedId.value) ?? null
);

/** La URL manda, igual que en moderación: el filtro se comparte y el back del
 * navegador lo deshace. La página sigue en memoria. */
const urlFilters = computed(() =>
  sanitizeFilterQuery(route.query, BULK_JOB_FILTERS)
);

function onApplyFilters(values: Record<string, string>) {
  router.push({ query: values });
}

watch(urlFilters, (filters) => applyFilters(filters), { immediate: true });
</script>
