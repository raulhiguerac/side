<template>
  <div class="w-full overflow-x-auto">
    <table class="w-full border-collapse text-sm">
      <thead>
        <tr
          v-for="headerGroup in table.getHeaderGroups()"
          :key="headerGroup.id"
          class="border-b border-brand-divider"
        >
          <th
            v-for="header in headerGroup.headers"
            :key="header.id"
            :class="[
              'py-3 px-4 text-xs font-semibold uppercase tracking-wide text-brand-muted whitespace-nowrap',
              alignOf(header.column.columnDef) === 'right'
                ? 'text-right'
                : 'text-left',
            ]"
          >
            <FlexRender
              :render="header.column.columnDef.header"
              :props="header.getContext()"
            />
          </th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="row in table.getRowModel().rows"
          :key="row.id"
          class="border-b border-brand-divider last:border-0 hover:bg-brand-bg transition-colors"
        >
          <td
            v-for="cell in row.getVisibleCells()"
            :key="cell.id"
            :class="[
              'py-3 px-4 text-brand-text align-middle',
              alignOf(cell.column.columnDef) === 'right'
                ? 'text-right'
                : 'text-left',
            ]"
          >
            <!--
              Cada slot se llama igual que su columna. El slot gana y FlexRender
              es el fallback: las columnas de texto plano no necesitan nada, y
              las que llevan badges o botones se escriben como template en el
              padre en vez de como render function dentro del columnDef.

              Sin prefijo a propósito: un nombre con `:` obligaría a la sintaxis
              de argumento dinámico (`#[\`cell:status\`]`) en cada uso. Si algún
              día hacen falta slots estructurales, se namespacean esos.
            -->
            <slot
              :name="cell.column.id"
              :row="row.original"
              :value="cell.getValue()"
            >
              <FlexRender
                :render="cell.column.columnDef.cell"
                :props="cell.getContext()"
              />
            </slot>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="loading" class="py-10 flex justify-center">
      <BaseSpinner class="h-6 w-6 text-brand-primary" />
    </div>

    <EmptyState
      v-else-if="!table.getRowModel().rows.length"
      :title="emptyTitle"
      :description="emptyDescription"
    />
  </div>
</template>

<script setup lang="ts" generic="T">
import {
  FlexRender,
  getCoreRowModel,
  useVueTable,
  type ColumnDef,
} from "@tanstack/vue-table";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import EmptyState from "@/components/shared/EmptyState.vue";

const props = withDefaults(
  defineProps<{
    columns: ColumnDef<T, any>[]; // eslint-disable-line @typescript-eslint/no-explicit-any
    data: T[];
    loading?: boolean;
    emptyTitle?: string;
    emptyDescription?: string;
  }>(),
  {
    loading: false,
    emptyTitle: "Nada por acá",
    emptyDescription: "No hay resultados para los filtros seleccionados.",
  }
);

/**
 * Los getters son la forma que pide el adaptador de Vue para que la tabla
 * reaccione a cambios de props: pasar `props.data` directo la congelaría en el
 * valor del primer render.
 *
 * Solo se registra el core row model. Ordenamiento, filtros y paginación son
 * server-side en este proyecto, así que sumar `getSortedRowModel` o
 * `getPaginationRowModel` haría que la tabla operara sobre la página ya cargada
 * y diera resultados que parecen globales sin serlo.
 */
const table = useVueTable({
  get data() {
    return props.data;
  },
  get columns() {
    return props.columns;
  },
  getCoreRowModel: getCoreRowModel(),
});

type ColumnAlign = "left" | "right";

function alignOf(columnDef: { meta?: unknown }): ColumnAlign {
  const meta = columnDef.meta as { align?: ColumnAlign } | undefined;
  return meta?.align ?? "left";
}
</script>
