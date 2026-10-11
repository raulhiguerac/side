<template>
  <BaseTable
    :columns="columns"
    :data="rows"
    :loading="loading"
    :row-key="(row: NeighborhoodAdminRow) => row.id"
    :selected-key="selectedId"
    empty-title="Sin barrios"
    empty-description="Ningún barrio coincide con los filtros seleccionados."
    @row-click="emit('rowClick', $event)"
  >
    <template #shape="{ row }">
      <NeighborhoodSilhouette :svg-path="row.svg_path" :bbox="row.bbox" />
    </template>

    <template #is_active="{ row }">
      <span
        :class="[
          'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
          row.is_active
            ? 'bg-brand-primary-light text-green-700'
            : 'bg-gray-100 text-brand-muted',
        ]"
      >
        {{ row.is_active ? "Activo" : "Inactivo" }}
      </span>
    </template>
  </BaseTable>
</template>

<script setup lang="ts">
import type { ColumnDef } from "@tanstack/vue-table";
import BaseTable from "@/components/shared/BaseTable.vue";
import NeighborhoodSilhouette from "@/components/admin/catalog/neighborhoods/widgets/NeighborhoodSilhouette.vue";
import type { NeighborhoodAdminRow } from "@/types/admin/catalog";

defineProps<{
  rows: NeighborhoodAdminRow[];
  loading?: boolean;
  selectedId?: string | null;
}>();

const emit = defineEmits<{ rowClick: [row: NeighborhoodAdminRow] }>();

const columns: ColumnDef<NeighborhoodAdminRow>[] = [
  { id: "shape", header: "Forma" },
  { id: "name", header: "Nombre", accessorKey: "name" },
  { id: "code", header: "Código", accessorKey: "code" },
  { id: "is_active", header: "Estado" },
];
</script>
