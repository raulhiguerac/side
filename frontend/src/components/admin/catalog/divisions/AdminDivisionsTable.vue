<template>
  <BaseTable
    :columns="columns"
    :data="rows"
    :loading="loading"
    :row-key="(row: DivisionAdminRow) => row.id"
    :selected-key="selectedId"
    empty-title="Sin divisiones"
    empty-description="Ninguna división coincide con los filtros seleccionados."
    @row-click="emit('rowClick', $event)"
  >
    <template #iso_code="{ row }">{{ row.iso_code ?? "—" }}</template>

    <template #is_active="{ row }">
      <AdminStatusBadge :active="row.is_active" />
    </template>
  </BaseTable>
</template>

<script setup lang="ts">
import type { ColumnDef } from "@tanstack/vue-table";
import AdminStatusBadge from "@/components/admin/shared/AdminStatusBadge.vue";
import BaseTable from "@/components/shared/BaseTable.vue";
import type { DivisionAdminRow } from "@/types/admin/catalog";

defineProps<{
  rows: DivisionAdminRow[];
  loading?: boolean;
  selectedId?: string | null;
}>();

const emit = defineEmits<{ rowClick: [row: DivisionAdminRow] }>();

const columns: ColumnDef<DivisionAdminRow>[] = [
  { id: "name", header: "Nombre", accessorKey: "name" },
  { id: "code", header: "Código", accessorKey: "code" },
  { id: "type_name", header: "Tipo", accessorKey: "type_name" },
  { id: "iso_code", header: "ISO" },
  { id: "is_active", header: "Estado" },
];
</script>
