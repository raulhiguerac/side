<template>
  <BaseTable
    :columns="columns"
    :data="rows"
    :loading="loading"
    :row-key="(row: LocalityAdminRow) => row.id"
    :selected-key="selectedId"
    empty-title="Sin localidades"
    empty-description="Ninguna localidad coincide con los filtros seleccionados."
    @row-click="emit('rowClick', $event)"
  >
    <template #name="{ row }">
      <span class="inline-flex items-center gap-1.5">
        {{ row.name }}
        <Star
          v-if="row.is_capital"
          class="h-3.5 w-3.5 fill-amber-400 text-amber-400"
          aria-label="Capital"
        />
      </span>
    </template>

    <template #locality_type="{ row }">
      {{ LOCALITY_TYPE_LABELS[row.locality_type] }}
    </template>

    <template #is_active="{ row }">
      <AdminStatusBadge :active="row.is_active" />
    </template>
  </BaseTable>
</template>

<script setup lang="ts">
import type { ColumnDef } from "@tanstack/vue-table";
import { Star } from "@lucide/vue";
import AdminStatusBadge from "@/components/admin/shared/AdminStatusBadge.vue";
import BaseTable from "@/components/shared/BaseTable.vue";
import { LOCALITY_TYPE_LABELS } from "@/constants/localityLabels";
import type { LocalityAdminRow } from "@/types/admin/catalog";

defineProps<{
  rows: LocalityAdminRow[];
  loading?: boolean;
  selectedId?: string | null;
}>();

const emit = defineEmits<{ rowClick: [row: LocalityAdminRow] }>();

const columns: ColumnDef<LocalityAdminRow>[] = [
  { id: "name", header: "Nombre" },
  { id: "code", header: "Código", accessorKey: "code" },
  { id: "locality_type", header: "Tipo" },
  { id: "is_active", header: "Estado" },
];
</script>
