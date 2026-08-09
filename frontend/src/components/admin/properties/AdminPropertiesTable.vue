<template>
  <BaseTable
    :columns="columns"
    :data="rows"
    :loading="loading"
    :row-key="(row: AdminPropertyRow) => row.id"
    :selected-key="selectedId"
    empty-title="Sin propiedades"
    empty-description="Ninguna propiedad coincide con los filtros seleccionados."
    @row-click="emit('rowClick', $event)"
  >
    <template #verification_status="{ row }">
      <span
        :class="[
          'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
          VERIFICATION_STATUS_BADGE_CLASSES[row.verification_status],
        ]"
      >
        {{ VERIFICATION_STATUS_LABELS[row.verification_status] }}
      </span>
      <p
        v-if="row.rejection_reason"
        class="mt-1 max-w-[220px] truncate text-xs text-brand-muted"
        :title="row.rejection_reason"
      >
        {{ row.rejection_reason }}
      </p>
    </template>

    <template #status="{ row }">
      <span
        :class="[
          'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
          LISTING_STATUS_BADGE_CLASSES[row.status],
        ]"
      >
        {{ LISTING_STATUS_LABELS[row.status] }}
      </span>
    </template>

    <template #price="{ row }">
      <span class="font-semibold tabular-nums">
        {{ formatCurrency(row.price, row.currency) }}
      </span>
    </template>

    <!-- No es recursión: `#actions` es el slot de BaseTable y el de adentro reenvía el del padre. -->
    <template v-if="slots.actions" #actions="{ row }">
      <slot name="actions" :row="row" />
    </template>
  </BaseTable>
</template>

<script setup lang="ts">
import { computed, useSlots } from "vue";
import type { ColumnDef } from "@tanstack/vue-table";
import BaseTable from "@/components/shared/BaseTable.vue";
import { formatCurrency } from "@/utils/money";
import { formatShortDate } from "@/utils/date";
import {
  LISTING_STATUS_LABELS,
  LISTING_STATUS_BADGE_CLASSES,
  VERIFICATION_STATUS_LABELS,
  VERIFICATION_STATUS_BADGE_CLASSES,
} from "@/constants/propertyStatus";
import type { AdminPropertyRow } from "@/types/admin";

defineProps<{
  rows: AdminPropertyRow[];
  loading?: boolean;
  selectedId?: string | null;
}>();

const emit = defineEmits<{ rowClick: [row: AdminPropertyRow] }>();

defineSlots<{
  actions?: (props: { row: AdminPropertyRow }) => unknown;
}>();

const slots = useSlots();

const PROPERTY_TYPE_LABELS: Record<AdminPropertyRow["property_type"], string> =
  {
    house: "Casa",
    apartment: "Apartamento",
  };

const LISTING_TYPE_LABELS: Record<AdminPropertyRow["listing_type"], string> = {
  sale: "Venta",
  rent: "Arriendo",
};

/** Solo campos para escanear y sin orden: identificar la property es del panel, y el listado no ordena. */
const columns = computed<ColumnDef<AdminPropertyRow>[]>(() => {
  const base: ColumnDef<AdminPropertyRow>[] = [
    { id: "verification_status", header: "Verificación" },
    {
      id: "property_type",
      header: "Tipo",
      accessorFn: (row) => PROPERTY_TYPE_LABELS[row.property_type],
    },
    {
      id: "listing_type",
      header: "Operación",
      accessorFn: (row) => LISTING_TYPE_LABELS[row.listing_type],
    },
    { id: "price", header: "Precio", meta: { align: "right" } },
    {
      id: "created_at",
      header: "Creada",
      accessorFn: (row) => formatShortDate(row.created_at),
    },
    { id: "status", header: "Estado" },
  ];

  return slots.actions
    ? [...base, { id: "actions", header: "", meta: { align: "right" } }]
    : base;
});
</script>
