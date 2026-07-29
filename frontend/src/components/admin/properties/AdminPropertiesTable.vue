<template>
  <BaseTable
    :columns="columns"
    :data="rows"
    :loading="loading"
    empty-title="Sin propiedades"
    empty-description="Ninguna propiedad coincide con los filtros seleccionados."
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

    <!--
      No es recursión: `#actions` es el slot de la columna en BaseTable, y el
      `<slot name="actions">` de adentro reenvía el que recibe este componente
      de su padre. Coinciden en nombre porque son de componentes distintos.
    -->
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
}>();

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

/**
 * Se muestran 5 de los 13 campos del schema. Meterlos todos mataría la
 * escaneabilidad, que es justamente el motivo de haber elegido tabla sobre el
 * card grid del feed: `id`/`owner_id` son UUIDs que no dicen nada sin un join
 * que hoy no existe, y área/habitaciones/baños son detalle, no moderación.
 *
 * Sin columnas ordenables: `GET /admin/properties` todavía no acepta parámetro
 * de orden, y ordenar client-side reordenaría solo la página cargada, dando un
 * resultado que parece global sin serlo.
 */
const columns = computed<ColumnDef<AdminPropertyRow>[]>(() => {
  const base: ColumnDef<AdminPropertyRow>[] = [
    { id: "verification_status", header: "Verificación" },
    {
      id: "tipo",
      header: "Tipo",
      accessorFn: (row) =>
        `${PROPERTY_TYPE_LABELS[row.property_type]} · ${
          LISTING_TYPE_LABELS[row.listing_type]
        }`,
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
