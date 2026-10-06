<template>
  <BaseTable
    :columns="columns"
    :data="rows"
    :loading="loading"
    :row-key="(row: AdminPromotionRow) => row.property_id"
    :selected-key="selectedId"
    empty-title="Sin promociones activas"
    empty-description="Ninguna propiedad está promocionada en este momento."
    @row-click="emit('rowClick', $event)"
  >
    <template #priority="{ row }">
      <span
        class="bg-brand-primary-light text-brand-primary inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold"
      >
        {{ row.priority }}
      </span>
    </template>

    <template #price="{ row }">
      <span class="font-semibold tabular-nums">
        {{
          row.property
            ? formatCurrency(row.property.price, row.property.currency)
            : "—"
        }}
      </span>
    </template>

    <template #ends_at="{ row }">
      <span class="tabular-nums">{{ formatShortDate(row.ends_at) }}</span>
      <p class="text-brand-muted text-xs">{{ daysLeftLabel(row.ends_at) }}</p>
    </template>
  </BaseTable>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ColumnDef } from "@tanstack/vue-table";
import BaseTable from "@/components/shared/BaseTable.vue";
import { formatCurrency } from "@/utils/money";
import { formatShortDate } from "@/utils/date";
import {
  LISTING_TYPE_LABELS,
  PROPERTY_TYPE_LABELS,
} from "@/constants/propertyLabels";
import type { AdminPromotionRow } from "@/types/admin/promotions";

// Filas de promociones: se selecciona por `property_id`, que es lo que pide el panel.
defineProps<{
  rows: AdminPromotionRow[];
  loading?: boolean;
  selectedId?: string | null;
}>();

const emit = defineEmits<{ rowClick: [row: AdminPromotionRow] }>();

/** El vencimiento en días es lo accionable; la fecha sola obliga a hacer la cuenta. */
function daysLeftLabel(endsAt: string): string {
  const days = Math.ceil(
    (new Date(endsAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );
  if (days < 0) return "vencida";
  if (days === 0) return "vence hoy";
  return `en ${days} ${days === 1 ? "día" : "días"}`;
}

const columns = computed<ColumnDef<AdminPromotionRow>[]>(() => [
  { id: "priority", header: "Prio." },
  {
    id: "property_type",
    header: "Tipo",
    accessorFn: (row) =>
      row.property ? PROPERTY_TYPE_LABELS[row.property.property_type] : "—",
  },
  {
    id: "listing_type",
    header: "Operación",
    accessorFn: (row) =>
      row.property ? LISTING_TYPE_LABELS[row.property.listing_type] : "—",
  },
  { id: "price", header: "Precio", meta: { align: "right" } },
  { id: "ends_at", header: "Vence" },
]);
</script>
