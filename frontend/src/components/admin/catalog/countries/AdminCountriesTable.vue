<template>
  <BaseTable
    :columns="columns"
    :data="rows"
    :loading="loading"
    :row-key="(row: CountryAdminRow) => row.id"
    :selected-key="selectedId"
    empty-title="Sin países"
    empty-description="Ningún país coincide con los filtros seleccionados."
    @row-click="emit('rowClick', $event)"
  >
    <template #is_supported="{ row }">
      {{ row.is_supported ? "Soportado" : "—" }}
    </template>

    <template #is_active="{ row }">
      <AdminStatusBadge :active="row.is_active" />
    </template>
  </BaseTable>
</template>

<script setup lang="ts">
import type { ColumnDef } from "@tanstack/vue-table";
import AdminStatusBadge from "@/components/admin/shared/AdminStatusBadge.vue";
import BaseTable from "@/components/shared/BaseTable.vue";
import type { CountryAdminRow } from "@/types/admin/catalog";

defineProps<{
  rows: CountryAdminRow[];
  loading?: boolean;
  selectedId?: string | null;
}>();

const emit = defineEmits<{ rowClick: [row: CountryAdminRow] }>();

const columns: ColumnDef<CountryAdminRow>[] = [
  { id: "name", header: "Nombre", accessorKey: "name" },
  { id: "iso_alpha2", header: "ISO", accessorKey: "iso_alpha2" },
  { id: "currency_code", header: "Moneda", accessorKey: "currency_code" },
  { id: "is_supported", header: "Soporte" },
  { id: "is_active", header: "Estado" },
];
</script>
