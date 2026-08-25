<template>
  <BaseTable
    :columns="columns"
    :data="rows"
    :loading="loading"
    :row-key="(row: BulkJobRow) => row.id"
    :selected-key="selectedId"
    empty-title="Sin importaciones"
    empty-description="Todavía no se ha importado ningún CSV."
    @row-click="emit('rowClick', $event)"
  >
    <template #id="{ row }">
      <span class="text-brand-text font-mono text-xs">
        {{ shortId(row.id) }}
      </span>
      <p v-if="row.retry_of_job_id" class="text-brand-muted mt-0.5 text-xs">
        reintento de {{ shortId(row.retry_of_job_id) }}
      </p>
    </template>

    <template #status="{ row }">
      <span
        :class="[
          'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
          BULK_JOB_STATUS_BADGE_CLASSES[row.status],
        ]"
      >
        {{ BULK_JOB_STATUS_LABELS[row.status] }}
      </span>
    </template>

    <template #inserted="{ row }">
      <span class="font-semibold tabular-nums">
        {{ row.inserted.toLocaleString("es-CO") }}
      </span>
    </template>

    <!-- El cero en gris: lo que hay que encontrar de un vistazo son las corridas con errores. -->
    <template #error_count="{ row }">
      <span
        :class="[
          'tabular-nums',
          row.error_count ? 'font-semibold text-red-600' : 'text-brand-muted',
        ]"
      >
        {{ row.error_count.toLocaleString("es-CO") }}
      </span>
    </template>

    <template #actions="{ row }">
      <button
        v-if="row.status !== 'pending'"
        type="button"
        title="Relanzar"
        class="text-brand-muted hover:text-brand-primary rounded-lg p-1.5 transition-colors hover:bg-gray-50"
      >
        <RotateCcw class="h-4 w-4" />
      </button>
    </template>
  </BaseTable>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { RotateCcw } from "@lucide/vue";
import BaseTable from "@/components/shared/BaseTable.vue";
import { formatShortDateTime } from "@/utils/date";
import {
  BULK_JOB_STATUS_LABELS,
  BULK_JOB_STATUS_BADGE_CLASSES,
} from "@/constants/bulkJobStatus";
import type { BulkJobRow } from "@/types/admin";

/** El historial de importaciones: qué corrió, cómo terminó y cuánto entró. */
defineProps<{
  rows: BulkJobRow[];
  loading?: boolean;
  selectedId?: string | null;
}>();

const emit = defineEmits<{ rowClick: [row: BulkJobRow] }>();

/** El uuid entero no cabe y nadie lo lee: los primeros 8 alcanzan para distinguir corridas. */
function shortId(id: string): string {
  return id.slice(0, 8);
}

const columns = computed<ColumnDef<BulkJobRow>[]>(() => [
  {
    id: "created_at",
    header: "Fecha",
    accessorFn: (row) => formatShortDateTime(row.created_at),
  },
  { id: "id", header: "Job" },
  { id: "status", header: "Estado" },
  { id: "inserted", header: "Cargadas", meta: { align: "right" } },
  { id: "error_count", header: "Errores", meta: { align: "right" } },
  { id: "actions", header: "", meta: { align: "right" } },
]);
</script>
